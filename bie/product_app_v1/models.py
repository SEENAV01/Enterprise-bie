from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import re

RUN_ID_RE = re.compile(r"^oprun-[0-9a-f]{64}$")
CREATE_KEY_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
SAFE_STATES = {
    "DRAFT", "READY", "ACTIVE", "PAUSED", "CANCELLED",
    "SUCCEEDED", "FAILED", "BLOCKED",
}
TERMINAL_STATES = {"CANCELLED", "SUCCEEDED", "FAILED", "BLOCKED"}


class OperatorError(ValueError):
    pass


class OperatorConflict(OperatorError):
    pass


def require_token(value: str, field: str, *, max_len: int = 256) -> str:
    if type(value) is not str:
        raise OperatorError(f"{field}_must_be_string")
    value = value.strip()
    if not value or len(value) > max_len or any(ord(ch) < 32 for ch in value):
        raise OperatorError(f"invalid_{field}")
    return value


@dataclass(frozen=True)
class RunSnapshot:
    run_id: str
    state: str
    attempt: int
    source_hash: str | None
    source_name: str | None
    canonical_job_id: str | None
    created_at: float
    updated_at: float

    def __post_init__(self) -> None:
        if not RUN_ID_RE.fullmatch(self.run_id):
            raise OperatorError("invalid_run_id")
        if self.state not in SAFE_STATES:
            raise OperatorError("invalid_run_state")
        if self.attempt < 0:
            raise OperatorError("invalid_attempt")
        if self.source_hash is not None:
            if len(self.source_hash) != 64 or any(c not in "0123456789abcdef" for c in self.source_hash):
                raise OperatorError("invalid_source_hash")

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "state": self.state,
            "attempt": self.attempt,
            "source_hash": self.source_hash,
            "source_name": self.source_name,
            "canonical_job_id": self.canonical_job_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "progress_percent": None,
        }


@dataclass(frozen=True)
class AttemptSnapshot:
    run_id: str
    attempt: int
    canonical_job_id: str
    idempotency_key: str
    source_hash: str
    state: str
    retry_of_job_id: str | None
    created_at: float


@dataclass(frozen=True)
class OperatorEvent:
    sequence: int
    run_id: str
    event_type: str
    created_at: float
    payload: dict[str, Any]

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "run_id": self.run_id,
            "event_type": self.event_type,
            "created_at": self.created_at,
            "payload": dict(self.payload),
        }
