"""Bounded POSIX child-process execution used by BUILD-007..009.

This is lifecycle control, NOT a security sandbox for untrusted JavaScript.
No shell, no implicit package download, sanitized environment, process-group kill.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from threading import Event
from typing import Iterable
import math
import os
import selectors
import signal
import subprocess
import time
from .build_common import BuildError, ProcessReceipt
from .render_logs import redact_text

@dataclass(frozen=True)
class RenderProcessResult:
    process: ProcessReceipt
    outcome: str
    started: bool
    stdout_bytes: int
    stderr_bytes: int
    accepted: bool = False

def _kill_group(process: subprocess.Popen, sig: int) -> None:
    try:
        os.killpg(process.pid, sig)
    except ProcessLookupError:
        pass

def run_bounded_process(command: Iterable[str], *, cwd: str | Path,
                        timeout_s: float, cancel_event: Event | None = None,
                        max_output_bytes: int = 2 * 1024 * 1024,
                        secrets: Iterable[str] = ()) -> RenderProcessResult:
    if os.name != "posix":
        raise BuildError("this process-group adapter requires POSIX; use a governed Windows adapter")
    command = tuple(str(x) for x in command)
    if not command or any("\0" in x for x in command):
        raise BuildError("invalid command")
    if isinstance(timeout_s, bool) or not isinstance(timeout_s, (int, float)) or not math.isfinite(timeout_s) or timeout_s <= 0:
        raise BuildError("timeout_s must be positive and finite")
    if type(max_output_bytes) is not int or max_output_bytes < 1:
        raise BuildError("max_output_bytes must be positive")
    cwd = Path(cwd).resolve()
    if not cwd.is_dir():
        raise BuildError("process cwd missing")
    secrets = tuple(secrets)
    start = time.monotonic()
    safe_command = tuple(redact_text(x, secrets) for x in command)
    def result(code: int, out: bytes, err: bytes, outcome: str, started: bool) -> RenderProcessResult:
        receipt = ProcessReceipt(safe_command, str(cwd), code,
                                 redact_text(out.decode("utf-8", errors="replace"), secrets),
                                 redact_text(err.decode("utf-8", errors="replace"), secrets),
                                 int((time.monotonic() - start) * 1000), outcome == "SUCCEEDED", False)
        return RenderProcessResult(receipt, outcome, started, len(out), len(err))
    if cancel_event is not None and cancel_event.is_set():
        return result(-1, b"", b"", "CANCELLED", False)
    allowed_env = {"PATH", "HOME", "LANG", "LC_ALL", "TMPDIR", "DISPLAY", "FONTCONFIG_PATH", "FONTCONFIG_FILE", "XDG_RUNTIME_DIR"}
    env = {k: v for k, v in os.environ.items() if k in allowed_env}
    env.update({"CI": "true", "NO_COLOR": "1"})
    try:
        process = subprocess.Popen(command, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   start_new_session=True, bufsize=0)
    except OSError as exc:
        return result(-1, b"", str(exc).encode(), "SPAWN_ERROR", False)
    captured = {"stdout": bytearray(), "stderr": bytearray()}
    outcome = None
    killed_at = None
    with selectors.DefaultSelector() as selector:
        for stream, name in ((process.stdout, "stdout"), (process.stderr, "stderr")):
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, name)
        try:
            while selector.get_map() or process.poll() is None:
                now = time.monotonic()
                if outcome is None:
                    if cancel_event is not None and cancel_event.is_set():
                        outcome = "CANCELLED"
                    elif now - start >= timeout_s:
                        outcome = "TIMED_OUT"
                    if outcome is not None:
                        _kill_group(process, signal.SIGTERM)
                        killed_at = now
                if killed_at is not None and now - killed_at > 0.25:
                    _kill_group(process, signal.SIGKILL)
                    if now - killed_at > 1.0:
                        break
                for key, _ in selector.select(0.025):
                    try:
                        chunk = os.read(key.fileobj.fileno(), 65536)
                    except BlockingIOError:
                        continue
                    if not chunk:
                        selector.unregister(key.fileobj)
                        key.fileobj.close()
                        continue
                    total = sum(len(v) for v in captured.values())
                    room = max(0, max_output_bytes - total)
                    captured[key.data].extend(chunk[:room])
                    if len(chunk) > room and outcome is None:
                        outcome = "OUTPUT_LIMIT"
                        killed_at = time.monotonic()
                        _kill_group(process, signal.SIGTERM)
            if outcome is not None:
                _kill_group(process, signal.SIGKILL)
            returncode = process.wait(timeout=2)
        finally:
            # Also close descendant processes that outlive the CLI's main process.
            _kill_group(process, signal.SIGKILL)
            if process.poll() is None:
                process.wait(timeout=2)
            for stream in (process.stdout, process.stderr):
                if stream is not None and not stream.closed:
                    stream.close()
    return result(returncode, bytes(captured["stdout"]), bytes(captured["stderr"]),
                  outcome or ("SUCCEEDED" if returncode == 0 else "FAILED"), True)
