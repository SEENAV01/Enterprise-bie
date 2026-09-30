from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


class AppProductError(ValueError):
    pass


class InvalidSource(AppProductError):
    def __init__(self, message: str, validation: "SourceValidation | None" = None):
        super().__init__(message)
        self.validation = validation


class ControlConflict(AppProductError):
    pass


class ProjectionError(AppProductError):
    pass


class GraphViewError(AppProductError):
    pass


def _bounded(value: str, field: str, *, maximum: int = 512) -> str:
    if type(value) is not str:
        raise AppProductError(f"{field}_must_be_string")
    value = value.strip()
    if not value or len(value) > maximum or any(ord(c) < 32 for c in value):
        raise AppProductError(f"invalid_{field}")
    return value


def _sha256(value: str, field: str = "sha256") -> str:
    value = _bounded(value, field, maximum=64)
    if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise AppProductError(f"invalid_{field}")
    return value


@dataclass(frozen=True)
class SourceValidation:
    status: str
    display_name: str
    media_type: str
    byte_length: int
    source_sha256: str | None
    issues: tuple[str, ...]
    warnings: tuple[str, ...]
    native_validation: str

    def __post_init__(self):
        if self.status not in {"READY_TO_SUBMIT", "REJECTED"}:
            raise AppProductError("invalid_source_validation_status")
        _bounded(self.display_name, "display_name", maximum=256)
        _bounded(self.media_type, "media_type", maximum=128)
        if type(self.byte_length) is not int or self.byte_length < 0:
            raise AppProductError("invalid_byte_length")
        if self.source_sha256 is not None:
            _sha256(self.source_sha256, "source_sha256")
        if self.native_validation not in {"PENDING", "NOT_RUN"}:
            raise AppProductError("invalid_native_validation")
        if self.status == "READY_TO_SUBMIT" and self.issues:
            raise AppProductError("ready_source_cannot_have_issues")

    def to_safe_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RunView:
    job_id: str
    status: str
    canonical_status: str
    queue_state: str
    source_hash: str
    result_available: bool
    control_state: str

    def __post_init__(self):
        _bounded(self.job_id, "job_id", maximum=80)
        _sha256(self.source_hash, "source_hash")
        if self.control_state not in {"ACTIVE", "PAUSED", "CANCELLED"}:
            raise AppProductError("invalid_control_state")

    def to_safe_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RunTimeline:
    job_id: str
    stage_events: tuple[dict[str, Any], ...]
    queue_events: tuple[dict[str, Any], ...]
    control_events: tuple[dict[str, Any], ...]

    def to_safe_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FailureView:
    job_id: str
    status: str
    diagnostics: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    evidence: tuple[dict[str, Any], ...]
    raw_source_exposed: bool = False

    def __post_init__(self):
        if self.status != "FAILED":
            raise ProjectionError("failure_view_requires_failed_run")
        if self.raw_source_exposed:
            raise ProjectionError("raw_source_exposure_forbidden")

    def to_safe_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ControlReceipt:
    job_id: str
    action: str
    state: str
    queue_state: str
    reason: str
    related_job_id: str | None = None

    def to_safe_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GraphNode:
    node_id: str
    label: str
    node_type: str
    is_root: bool = False
    is_leaf: bool = False


@dataclass(frozen=True)
class GraphEdge:
    source: str
    target: str
    relation: str
    confidence: float | None = None


@dataclass(frozen=True)
class GraphView:
    graph_type: str
    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...]
    order: tuple[str, ...] = ()
    source_status: str = "CANONICAL_TYPED_INPUT"

    def __post_init__(self):
        if self.graph_type not in {"concept", "prerequisite"}:
            raise GraphViewError("unknown_graph_type")
        if self.source_status != "CANONICAL_TYPED_INPUT":
            raise GraphViewError("untrusted_graph_source")

    def to_safe_dict(self) -> dict[str, Any]:
        return asdict(self)
