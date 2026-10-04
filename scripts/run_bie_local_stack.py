"""Supervise the loopback apps/api server and continuous /v1/jobs PDF worker.

This launcher does not launch or control Section18 operator processes.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import ipaddress
import json
import math
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import threading
import time
from urllib.request import ProxyHandler, HTTPRedirectHandler, build_opener

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.pdf_worker_service import (
    api_worker_root, stop_on_stdin_eof, stop_signals, validate_poll_interval,
)


class StackError(RuntimeError):
    pass


@dataclass(frozen=True)
class StackConfig:
    host: str = "127.0.0.1"
    port: int = 8000
    poll_interval: float = 1.0
    readiness_timeout: float = 20.0
    shutdown_grace: float = 20.0

    def __post_init__(self):
        try:
            address = ipaddress.ip_address(self.host)
        except ValueError:
            raise ValueError("invalid_loopback_host") from None
        if not address.is_loopback or "%" in self.host:
            raise ValueError("invalid_loopback_host")
        if isinstance(self.port, bool) or not isinstance(self.port, int) or not 1 <= self.port <= 65535:
            raise ValueError("invalid_port")
        validate_poll_interval(self.poll_interval)
        for value in (self.readiness_timeout, self.shutdown_grace):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0.1 <= value <= 120:
                raise ValueError("invalid_process_timeout")


def child_commands(config: StackConfig) -> tuple[list[str], list[str]]:
    return (
        [sys.executable, str(ROOT / "scripts/run_bie_api.py"), "--host", config.host, "--port", str(config.port)],
        [sys.executable, str(ROOT / "scripts/run_bie_pdf_worker.py"), "--serve", "--poll-interval", str(config.poll_interval)],
    )


def child_environment(root: Path) -> dict[str, str]:
    return {**os.environ, "BIE_DATA_ROOT": str(api_worker_root(root)),
            "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUNBUFFERED": "1"}


def assert_port_available(config: StackConfig) -> None:
    family = socket.AF_INET6 if ":" in config.host else socket.AF_INET
    with socket.socket(family, socket.SOCK_STREAM) as sock:
        if os.name == "nt":
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        sock.bind((config.host, config.port))


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def healthy(config: StackConfig, timeout: float) -> bool:
    host = f"[{config.host}]" if ":" in config.host else config.host
    try:
        with build_opener(ProxyHandler({}), NoRedirect()).open(
            f"http://{host}:{config.port}/healthz", timeout=timeout,
        ) as response:
            payload = response.read(4097)
            return (response.status == 200 and len(payload) <= 4096 and json.loads(payload) ==
                    {"status": "ok", "service": "bie-api", "api_version": "v1"})
    except Exception:
        return False


def wait_ready(api, stop, config, *, clock=time.monotonic, probe=healthy) -> None:
    deadline = clock() + config.readiness_timeout
    while not stop.is_set():
        if api.poll() is not None:
            raise StackError("api_exited")
        remaining = deadline - clock()
        if remaining <= 0:
            raise StackError("readiness_timeout")
        if probe(config, min(0.5, remaining)) and api.poll() is None:
            return
        stop.wait(min(0.1, max(0, deadline - clock())))
    raise StackError("stop_requested")


def shutdown(children, grace: float) -> bool:
    """Cooperate first, then bounded terminate/kill; always reap owned children."""
    forced = False
    for process in children:
        if process.stdin is not None:
            try:
                process.stdin.close()  # worker's private cooperative stop channel
            except (OSError, ValueError):
                pass
        if process.poll() is None:
            try:
                process.send_signal(signal.CTRL_BREAK_EVENT if os.name == "nt" else signal.SIGINT)
            except (OSError, ValueError):
                pass  # consoleless Windows: wait grace, then bounded escalation
    deadline = time.monotonic() + grace
    for process in children:
        try:
            process.wait(timeout=max(0, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            pass
    for process in children:
        if process.poll() is None:
            forced = True
            try:
                process.terminate()
            except OSError:
                pass
    deadline = time.monotonic() + 3.0
    for process in children:
        try:
            process.wait(timeout=max(0, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3.0)
    return forced


def emit(value):
    print(json.dumps(value, sort_keys=True, separators=(",", ":")), flush=True)


def run_stack(config: StackConfig, stop: threading.Event, *, popen=subprocess.Popen,
              readiness=wait_ready, report=emit) -> int:
    children = []
    reason = "startup_failed"
    result = 1
    try:
        root = api_worker_root()
        env = child_environment(root)
        assert_port_available(config)
        if stop.is_set():
            reason, result = "requested", 0
            return result
        options = dict(cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       env=env, close_fds=True)
        if os.name == "nt":
            options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            options["start_new_session"] = True
        api_command, worker_command = child_commands(config)
        api = popen(api_command, stdin=subprocess.DEVNULL, **options)
        children.append(api)
        readiness(api, stop, config)
        if stop.is_set():
            reason, result = "requested", 0
            return result
        worker_options = {**options, "env": {**env, "BIE_PDF_WORKER_CONTROL_STDIN": "1"}}
        worker = popen(worker_command, stdin=subprocess.PIPE, **worker_options)
        children.append(worker)
        report({"event": "stack_ready", "service": "bie-api", "worker": "apps_api_pdf",
                "host": config.host, "port": config.port})
        while not stop.is_set():
            if api.poll() is not None:
                reason = "api_exited"
                return 1
            if worker.poll() is not None:
                reason = "worker_exited"
                return 1
            stop.wait(0.1)
        reason, result = "requested", 0
        return result
    except StackError as exc:
        if str(exc) == "stop_requested":
            reason, result = "requested", 0
        elif str(exc) in {"readiness_timeout", "api_exited"}:
            reason = str(exc)
        return result
    except Exception:
        return 1
    finally:
        forced = shutdown(children, config.shutdown_grace)
        report({"event": "stack_stopped", "reason": reason,
                "children_reaped": all(p.poll() is not None for p in children),
                "forced_termination": forced})


class SafeParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, "Invalid local stack arguments\n")


def main(argv: list[str] | None = None) -> int:
    parser = SafeParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--poll-interval", type=float, default=1.0)
    parser.add_argument("--readiness-timeout", type=float, default=20.0)
    parser.add_argument("--shutdown-grace", type=float, default=20.0)
    args = parser.parse_args(argv)
    try:
        config = StackConfig(**vars(args))
    except ValueError:
        parser.error("invalid_configuration")
    stop = threading.Event()
    with stop_signals(stop):
        if os.environ.get("BIE_LOCAL_STACK_CONTROL_STDIN") == "1":
            stop_on_stdin_eof(stop, sys.stdin)
        return run_stack(config, stop)


if __name__ == "__main__":
    raise SystemExit(main())
