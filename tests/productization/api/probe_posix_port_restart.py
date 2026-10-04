"""R1 Linux-only, real TCP experiment; never changes production socket policy.

The original listener uses SO_REUSEADDR, like the existing Uvicorn listener.
The server actively closes its accepted connection: FIN -> peer EOF -> peer
FIN -> server EOF. A single /proc/net/tcp snapshot then checks the exact tuple
for TIME_WAIT (06) and the listening address for absence of LISTEN (0A).
There are no sleeps or retry loops. NOT_REPRODUCED is a valid diagnostic result,
not authorization to repair production. Raw proc rows and exceptions never leave
the diagnostic. The core experiment is not mocked.
"""
from __future__ import annotations

import argparse
from contextlib import ExitStack
import errno
import json
from pathlib import Path
import socket
import sys

ROOT = Path(__file__).resolve().parents[3]
LOOPBACK = "127.0.0.1"
PROC_LOOPBACK = "0100007F"


def tuple_states(snapshot: str, port: int, peer_port: int | None = None) -> set[str]:
    """Select only this experiment's IPv4 loopback socket, never output rows."""
    states = set()
    for line in snapshot.splitlines()[1:]:
        columns = line.split()
        if len(columns) < 4 or columns[1] != f"{PROC_LOOPBACK}:{port:04X}":
            continue
        if peer_port is not None and columns[2] != f"{PROC_LOOPBACK}:{peer_port:04X}":
            continue
        states.add(columns[3])
    return states


def tcp_snapshot() -> str:
    with open("/proc/net/tcp", "r", encoding="ascii") as stream:
        snapshot = stream.read(2 * 1024**2 + 1)
    if len(snapshot) > 2 * 1024**2:
        raise RuntimeError("bounded proc snapshot unavailable")
    return snapshot


def bind_result(port: int, *, reuse: bool = False) -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        if reuse:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind((LOOPBACK, port))
        except OSError as exc:
            return "EADDRINUSE" if exc.errno == errno.EADDRINUSE else "OTHER_ERROR"
    return "SUCCESS"


def current_preflight_result(port: int) -> str:
    # Execute the unchanged Task028 production preflight, not a copied repair.
    sys.path.insert(0, str(ROOT))
    from scripts.run_bie_local_stack import StackConfig, assert_port_available
    try:
        assert_port_available(StackConfig(port=port))
    except OSError as exc:
        return "EADDRINUSE" if exc.errno == errno.EADDRINUSE else "OTHER_ERROR"
    return "SUCCESS"


def reproduced(result: dict) -> bool:
    required = (
        "active_listener_plain_bind_rejected", "genuine_connection_accepted",
        "payload_exchange_verified", "close_order_verified", "listener_closed",
        "no_active_listener_observed", "connection_refused_after_close",
        "time_wait_condition_observed", "active_listener_reuseaddr_bind_rejected",
    )
    return (all(result.get(key) is True for key in required)
            and result.get("closed_listener_plain_bind") == "EADDRINUSE"
            and result.get("current_production_preflight") == "EADDRINUSE"
            and result.get("closed_listener_reuseaddr_bind") == "SUCCESS")


def run_probe() -> dict:
    result = {
        "platform": "linux" if sys.platform.startswith("linux") else "unsupported",
        "diagnostic_completed": False, "outcome": "NOT_RUN",
        "active_listener_plain_bind_rejected": False,
        "genuine_connection_accepted": False, "payload_exchange_verified": False,
        "close_order": "SERVER_FIN_PEER_EOF_PEER_FIN_SERVER_EOF",
        "close_order_verified": False, "listener_closed": False,
        "no_active_listener_observed": False, "connection_refused_after_close": False,
        "closed_listener_plain_bind": "NOT_RUN",
        "current_production_preflight": "NOT_RUN",
        "closed_listener_reuseaddr_bind": "NOT_RUN",
        "active_listener_reuseaddr_bind_rejected": False,
        "time_wait_condition_observed": False, "suspected_defect_reproduced": False,
        "original_listener_reuseaddr": True, "sleep_or_retry_used": False,
        "production_modified": False, "historical_hosted_cause_proven": False,
    }
    if result["platform"] != "linux":
        result["outcome"] = "NOT_AVAILABLE"
        return result
    phase = "listener"
    try:
        with ExitStack() as cleanup:
            listener = cleanup.enter_context(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
            listener.settimeout(3)
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener.bind((LOOPBACK, 0))
            listener.listen(1)
            port = listener.getsockname()[1]
            result["active_listener_plain_bind_rejected"] = bind_result(port) == "EADDRINUSE"
            phase = "connection"
            client = cleanup.enter_context(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
            client.settimeout(3)
            client.connect((LOOPBACK, port))
            accepted, peer = listener.accept()
            cleanup.enter_context(accepted)
            accepted.settimeout(3)
            result["genuine_connection_accepted"] = peer == client.getsockname()
            peer_port = peer[1]
            client.sendall(b"C")
            received_client = accepted.recv(1)
            accepted.sendall(b"S")
            result["payload_exchange_verified"] = received_client == b"C" and client.recv(1) == b"S"
            phase = "close_order"
            accepted.shutdown(socket.SHUT_WR)
            peer_eof = client.recv(1) == b""
            client.shutdown(socket.SHUT_WR)
            server_eof = accepted.recv(1) == b""
            result["close_order_verified"] = peer_eof and server_eof
            accepted.close()
            client.close()
            listener.close()
            result["listener_closed"] = listener.fileno() == -1
            phase = "tcp_state"
            snapshot = tcp_snapshot()
            result["no_active_listener_observed"] = "0A" not in tuple_states(snapshot, port)
            result["time_wait_condition_observed"] = "06" in tuple_states(snapshot, port, peer_port)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connection_probe:
                connection_probe.settimeout(3)
                result["connection_refused_after_close"] = connection_probe.connect_ex((LOOPBACK, port)) == errno.ECONNREFUSED
            phase = "closed_bind"
            result["closed_listener_plain_bind"] = bind_result(port)
            result["current_production_preflight"] = current_preflight_result(port)
            result["closed_listener_reuseaddr_bind"] = bind_result(port, reuse=True)
            phase = "active_collision"
            # Strong control: even the still-active listener itself allows reuse.
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as active:
                active.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                active.bind((LOOPBACK, 0))
                active.listen(1)
                result["active_listener_reuseaddr_bind_rejected"] = bind_result(active.getsockname()[1], reuse=True) == "EADDRINUSE"
        result["diagnostic_completed"] = True
        result["suspected_defect_reproduced"] = reproduced(result)
        result["outcome"] = "REPRODUCED" if result["suspected_defect_reproduced"] else "NOT_REPRODUCED"
    except Exception:
        # phase is assigned only literal values above; no exception text escapes.
        result["outcome"] = "NOT_REPRODUCED"
        result["error_code"] = "probe_" + phase + "_failed"
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    result = run_probe()
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    except Exception:
        print('{"diagnostic_completed":false,"error_code":"probe_evidence_write_failed"}')
        return 1
    print(encoded, end="")
    # A reproduced bug is evidence, not an intentionally failing regression.
    # A completed NOT_REPRODUCED experiment is also recorded truthfully.
    return 0 if result["diagnostic_completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
