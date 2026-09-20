from __future__ import annotations

from dataclasses import dataclass, field, replace
from hashlib import sha256
from math import isfinite
from typing import Any, Iterable, Mapping, Sequence
import json


class LayoutValidationError(ValueError):
    """Base deterministic layout validation failure."""


class LayoutGeometryError(LayoutValidationError):
    pass


class LayoutEvidenceError(LayoutValidationError):
    pass


def _token(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise LayoutValidationError(f"{field_name} must be a string")
    value = value.strip()
    if not value:
        raise LayoutValidationError(f"{field_name} must not be blank")
    return value


def clean_ids(values: Iterable[Any] | None, *, field_name: str, allow_empty: bool = False) -> tuple[str, ...]:
    values = () if values is None else values
    cleaned = tuple(_token(v, field_name=field_name) for v in values)
    if not allow_empty and not cleaned:
        raise LayoutValidationError(f"{field_name} must contain at least one id")
    if len(set(cleaned)) != len(cleaned):
        raise LayoutValidationError(f"{field_name} contains duplicate ids")
    return cleaned


def finite(value: Any, *, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise LayoutValidationError(f"{field_name} must be numeric")
    out = float(value)
    if not isfinite(out):
        raise LayoutValidationError(f"{field_name} must be finite")
    return out


def canonical_payload(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): canonical_payload(value[k]) for k in sorted(value, key=lambda x: str(x))}
    if isinstance(value, (list, tuple)):
        return [canonical_payload(v) for v in value]
    if isinstance(value, set):
        return sorted(canonical_payload(v) for v in value)
    if isinstance(value, float):
        if not isfinite(value):
            raise LayoutValidationError("payload contains non-finite float")
        return value
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise LayoutValidationError(f"unsupported payload type: {type(value).__name__}")


def stable_fingerprint(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(canonical_payload(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Box:
    x: float
    y: float
    width: float
    height: float

    def __post_init__(self) -> None:
        vals = [finite(self.x, field_name="box.x"), finite(self.y, field_name="box.y"),
                finite(self.width, field_name="box.width"), finite(self.height, field_name="box.height")]
        x, y, w, h = vals
        if w <= 0 or h <= 0:
            raise LayoutGeometryError("box width and height must be > 0")
        if x < 0 or y < 0 or x + w > 1.0 + 1e-9 or y + h > 1.0 + 1e-9:
            raise LayoutGeometryError("box must stay inside normalized [0,1] canvas")
        object.__setattr__(self, "x", x); object.__setattr__(self, "y", y)
        object.__setattr__(self, "width", w); object.__setattr__(self, "height", h)

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.y + self.height

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def center(self) -> tuple[float, float]:
        return (self.x + self.width / 2.0, self.y + self.height / 2.0)

    def contains(self, other: "Box", *, tolerance: float = 1e-9) -> bool:
        return (
            other.x >= self.x - tolerance
            and other.y >= self.y - tolerance
            and other.right <= self.right + tolerance
            and other.bottom <= self.bottom + tolerance
        )

    def intersection_area(self, other: "Box") -> float:
        w = max(0.0, min(self.right, other.right) - max(self.x, other.x))
        h = max(0.0, min(self.bottom, other.bottom) - max(self.y, other.y))
        return w * h

    def overlaps(self, other: "Box", *, tolerance: float = 1e-9) -> bool:
        return self.intersection_area(other) > tolerance

    def expand(self, margin: float) -> "Box":
        m = finite(margin, field_name="margin")
        if m < 0:
            raise LayoutGeometryError("margin must be >= 0")
        x = max(0.0, self.x - m); y = max(0.0, self.y - m)
        r = min(1.0, self.right + m); b = min(1.0, self.bottom + m)
        return Box(x, y, r - x, b - y)

    def to_dict(self) -> dict[str, float]:
        return {"x": self.x, "y": self.y, "width": self.width, "height": self.height}


@dataclass(frozen=True)
class LayoutNode:
    node_id: str
    role: str
    box: Box
    source_ids: tuple[str, ...]
    priority: int = 50
    required: bool = True
    group_id: str | None = None
    parent_id: str | None = None
    tags: tuple[str, ...] = ()
    payload: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "node_id", _token(self.node_id, field_name="node_id"))
        object.__setattr__(self, "role", _token(self.role, field_name=f"{self.node_id}.role"))
        object.__setattr__(self, "source_ids", clean_ids(self.source_ids, field_name=f"{self.node_id}.source_ids"))
        if isinstance(self.priority, bool) or not isinstance(self.priority, int) or not 0 <= self.priority <= 100:
            raise LayoutValidationError("priority must be an integer in [0,100]")
        if self.group_id is not None:
            object.__setattr__(self, "group_id", _token(self.group_id, field_name=f"{self.node_id}.group_id"))
        if self.parent_id is not None:
            object.__setattr__(self, "parent_id", _token(self.parent_id, field_name=f"{self.node_id}.parent_id"))
        object.__setattr__(self, "tags", clean_ids(self.tags, field_name=f"{self.node_id}.tags", allow_empty=True))
        object.__setattr__(self, "payload", canonical_payload(dict(self.payload)))

    def with_box(self, box: Box) -> "LayoutNode":
        return replace(self, box=box)

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "role": self.role,
            "box": self.box.to_dict(),
            "source_ids": list(self.source_ids),
            "priority": self.priority,
            "required": self.required,
            "group_id": self.group_id,
            "parent_id": self.parent_id,
            "tags": list(self.tags),
            "payload": canonical_payload(self.payload),
        }


@dataclass(frozen=True)
class LayoutPlan:
    evidence_refs: tuple[str, ...]
    reasoning_refs: tuple[str, ...]
    nodes: tuple[LayoutNode, ...]
    constraints: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    review_required: bool = True
    accepted: bool = False
    fingerprint: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_refs": list(self.evidence_refs),
            "reasoning_refs": list(self.reasoning_refs),
            "nodes": [n.to_dict() for n in self.nodes],
            "constraints": list(self.constraints),
            "warnings": list(self.warnings),
            "review_required": self.review_required,
            "accepted": self.accepted,
            "fingerprint": self.fingerprint,
        }


def make_layout_plan(
    *,
    evidence_refs: Sequence[str],
    reasoning_refs: Sequence[str],
    nodes: Sequence[LayoutNode],
    constraints: Sequence[str] = (),
    warnings: Sequence[str] = (),
) -> LayoutPlan:
    evidence = clean_ids(evidence_refs, field_name="evidence_refs")
    reasoning = clean_ids(reasoning_refs, field_name="reasoning_refs")
    node_tuple = tuple(nodes)
    if not node_tuple:
        raise LayoutValidationError("layout must contain at least one node")
    ids = [n.node_id for n in node_tuple]
    if len(ids) != len(set(ids)):
        raise LayoutValidationError("layout node ids must be unique")
    evidence_set = set(evidence)
    id_set = set(ids)
    for node in node_tuple:
        unknown = set(node.source_ids) - evidence_set
        if unknown:
            raise LayoutEvidenceError(f"node {node.node_id} has unbound source ids: {sorted(unknown)}")
        if node.parent_id is not None and node.parent_id not in id_set:
            raise LayoutValidationError(f"node {node.node_id} references unknown parent {node.parent_id}")
        if node.parent_id == node.node_id:
            raise LayoutValidationError("node cannot parent itself")
    # Parent cycle check.
    parents = {n.node_id: n.parent_id for n in node_tuple if n.parent_id is not None}
    for start in ids:
        seen = set()
        cur = start
        while cur in parents:
            if cur in seen:
                raise LayoutValidationError("parent hierarchy contains a cycle")
            seen.add(cur)
            cur = parents[cur]
    c = clean_ids(constraints, field_name="constraints", allow_empty=True)
    w = clean_ids(warnings, field_name="warnings", allow_empty=True)
    payload = {
        "evidence_refs": evidence,
        "reasoning_refs": reasoning,
        "nodes": [n.to_dict() for n in node_tuple],
        "constraints": c,
        "warnings": w,
        "review_required": True,
        "accepted": False,
    }
    return LayoutPlan(evidence, reasoning, node_tuple, c, w, True, False, stable_fingerprint(payload))


def plan_with_nodes(plan: LayoutPlan, nodes: Sequence[LayoutNode], *, warnings: Sequence[str] | None = None,
                    constraints: Sequence[str] | None = None) -> LayoutPlan:
    return make_layout_plan(
        evidence_refs=plan.evidence_refs,
        reasoning_refs=plan.reasoning_refs,
        nodes=nodes,
        constraints=plan.constraints if constraints is None else constraints,
        warnings=plan.warnings if warnings is None else warnings,
    )
