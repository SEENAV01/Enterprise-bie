"""BUILD-009: redacted, append-only, hash-chained render events."""
from __future__ import annotations
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable
import json
import os
import re
import time
from .artifact_hashing import canonical_json
from .build_common import BuildError

_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}$")
_ANSI = re.compile(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))")
_BEARER = re.compile(r"(?i)\b(Bearer|Basic)\s+[A-Za-z0-9+/_.=:-]+")
_KV = re.compile(r'''(?i)(["']?(?:api[-_]?key|access[-_]?token|refresh[-_]?token|token|secret|password|authorization|x-amz-signature|signature)["']?\s*[:=]\s*["']?)([^\s"'&,;\}\]]+)''')
_URL_AUTH = re.compile(r"(https?://)[^/\s:@]+:[^/\s@]+@", re.I)

def safe_token(value: str, name: str = "identifier") -> str:
    if not isinstance(value, str) or not _TOKEN.fullmatch(value):
        raise BuildError(f"invalid {name}")
    return value

def redact_text(value: str, secrets: Iterable[str] = ()) -> str:
    text = _ANSI.sub("", str(value))
    # Longest literal first so one supplied secret cannot partly expose another.
    for secret in sorted(set(s for s in secrets if isinstance(s, str) and s), key=len, reverse=True):
        text = text.replace(secret, "[REDACTED]")
    text = _BEARER.sub(lambda m: m.group(1) + " [REDACTED]", text)
    text = _URL_AUTH.sub(r"\1[REDACTED]@", text)
    return _KV.sub(lambda m: m.group(1) + "[REDACTED]", text)

def sanitize(value: Any, secrets: Iterable[str] = ()) -> Any:
    if isinstance(value, str):
        return redact_text(value, secrets)
    if isinstance(value, dict):
        return {str(k): ("[REDACTED]" if re.search(r"(?i)(secret|password|token|api.?key|authorization)", str(k))
                         else sanitize(v, secrets)) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [sanitize(v, secrets) for v in value]
    return value

class RenderEventLog:
    def __init__(self, path: str | Path, run_id: str, *, secrets: Iterable[str] = ()) -> None:
        self.path = Path(path)
        self.run_id = safe_token(run_id, "run_id")
        self.secrets = tuple(secrets)
        self.sequence = 0
        self.previous = "0" * 64
        self.started = time.monotonic()
        self.terminal = False
        # Caller owns a newly created, confined attempt directory.
        self._stream = self.path.open("x", encoding="utf-8", newline="\n")
        if os.name == "posix":
            os.chmod(self.path, 0o600)

    def append(self, event: str, status: str, details: dict | None = None) -> dict:
        if self.terminal:
            raise BuildError("cannot append after terminal render event")
        safe_token(event, "event")
        if status not in {"STARTED", "PASS", "FAIL", "CANCELLED", "BLOCKED", "INFO"}:
            raise BuildError("unknown event status")
        if event == "terminal" and status not in {"PASS", "FAIL", "CANCELLED", "BLOCKED"}:
            raise BuildError("terminal event must close the attempt")
        body = {"schema_version": "bie.render-event.v1", "run_id": self.run_id,
                "sequence": self.sequence, "elapsed_ms": int((time.monotonic() - self.started) * 1000),
                "event": event, "status": status, "details": sanitize(details or {}, self.secrets),
                "previous_sha256": self.previous}
        digest = sha256(canonical_json(body)).hexdigest()
        record = {**body, "event_sha256": digest}
        self._stream.write(canonical_json(record).decode("utf-8") + "\n")
        self._stream.flush()
        self.sequence += 1
        self.previous = digest
        if event == "terminal":
            os.fsync(self._stream.fileno())
            self.terminal = True
        return record

    def close(self) -> None:
        self._stream.close()

    def __enter__(self) -> "RenderEventLog":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

def verify_render_log(path: str | Path, *, require_terminal: bool = True) -> bool:
    previous = "0" * 64
    run_id = None
    last_elapsed = -1
    terminal = False
    count = 0
    try:
        with Path(path).open(encoding="utf-8") as stream:
            for sequence, line in enumerate(stream):
                if len(line) > 4 * 1024 * 1024 or terminal:
                    return False
                record = json.loads(line)
                digest = record.pop("event_sha256")
                expected_keys = {"schema_version", "run_id", "sequence", "elapsed_ms", "event", "status", "details", "previous_sha256"}
                if (set(record) != expected_keys or record["schema_version"] != "bie.render-event.v1"
                        or type(record["sequence"]) is not int or record["sequence"] != sequence or record["previous_sha256"] != previous
                        or type(record["elapsed_ms"]) is not int or record["elapsed_ms"] < last_elapsed
                        or record["status"] not in {"STARTED", "PASS", "FAIL", "CANCELLED", "BLOCKED", "INFO"}
                        or not isinstance(record["details"], dict)):
                    return False
                safe_token(record["run_id"], "run_id")
                safe_token(record["event"], "event")
                run_id = run_id or record["run_id"]
                if record["run_id"] != run_id or sha256(canonical_json(record)).hexdigest() != digest:
                    return False
                if record["event"] == "terminal":
                    if record["status"] not in {"PASS", "FAIL", "CANCELLED", "BLOCKED"}:
                        return False
                    terminal = True
                previous = digest
                last_elapsed = record["elapsed_ms"]
                count += 1
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return False
    return count > 0 and (terminal or not require_terminal)
