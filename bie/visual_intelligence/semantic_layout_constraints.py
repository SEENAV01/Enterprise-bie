from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .layout_contracts import Box, LayoutNode, LayoutPlan, LayoutValidationError, finite


class ConstraintError(LayoutValidationError):
    pass


@dataclass(frozen=True)
class ConstraintViolation:
    constraint_id: str
    kind: str
    node_ids: tuple[str, ...]
    magnitude: float
    message: str


ALLOWED_KINDS = {
    "non_overlap", "contains", "left_of", "above", "align_left",
    "align_top", "min_gap_x", "min_gap_y", "min_width", "min_height",
}


def _node_map(plan: LayoutPlan) -> dict[str, LayoutNode]:
    return {n.node_id: n for n in plan.nodes}


def validate_constraint_spec(spec: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(spec, Mapping):
        raise ConstraintError("constraint must be a mapping")
    cid = str(spec.get("id", "")).strip()
    kind = str(spec.get("kind", "")).strip()
    if not cid or kind not in ALLOWED_KINDS:
        raise ConstraintError("constraint requires a nonblank id and supported kind")
    nodes = tuple(str(x).strip() for x in spec.get("nodes", ()) if str(x).strip())
    if not nodes:
        raise ConstraintError("constraint requires node ids")
    value = spec.get("value")
    if value is not None:
        value = finite(value, field_name=f"{cid}.value")
        if value < 0:
            raise ConstraintError("constraint value must be >= 0")
    return {"id": cid, "kind": kind, "nodes": nodes, "value": value}


def evaluate_constraints(plan: LayoutPlan, specs: Sequence[Mapping[str, Any]], *, tolerance: float = 1e-6) -> tuple[ConstraintViolation, ...]:
    nodes = _node_map(plan)
    out: list[ConstraintViolation] = []
    seen = set()
    for raw in specs:
        spec = validate_constraint_spec(raw)
        if spec["id"] in seen:
            raise ConstraintError("constraint ids must be unique")
        seen.add(spec["id"])
        missing = [nid for nid in spec["nodes"] if nid not in nodes]
        if missing:
            raise ConstraintError(f"constraint {spec['id']} references unknown nodes: {missing}")
        ns = [nodes[nid] for nid in spec["nodes"]]
        kind = spec["kind"]; value = spec["value"]
        mag = 0.0
        if kind == "non_overlap":
            if len(ns) != 2: raise ConstraintError("non_overlap requires exactly two nodes")
            mag = ns[0].box.intersection_area(ns[1].box)
        elif kind == "contains":
            if len(ns) != 2: raise ConstraintError("contains requires parent, child")
            if not ns[0].box.contains(ns[1].box):
                b, c = ns[0].box, ns[1].box
                mag = max(b.x-c.x, b.y-c.y, c.right-b.right, c.bottom-b.bottom, 0.0)
        elif kind == "left_of":
            if len(ns) != 2: raise ConstraintError("left_of requires two nodes")
            mag = max(0.0, ns[0].box.right - ns[1].box.x + (value or 0.0))
        elif kind == "above":
            if len(ns) != 2: raise ConstraintError("above requires two nodes")
            mag = max(0.0, ns[0].box.bottom - ns[1].box.y + (value or 0.0))
        elif kind == "align_left":
            if len(ns) < 2: raise ConstraintError("align_left requires >=2 nodes")
            mag = max(abs(n.box.x - ns[0].box.x) for n in ns[1:])
        elif kind == "align_top":
            if len(ns) < 2: raise ConstraintError("align_top requires >=2 nodes")
            mag = max(abs(n.box.y - ns[0].box.y) for n in ns[1:])
        elif kind == "min_gap_x":
            if len(ns) != 2 or value is None: raise ConstraintError("min_gap_x requires two nodes and value")
            left, right = sorted(ns, key=lambda n: n.box.x)
            mag = max(0.0, value - (right.box.x - left.box.right))
        elif kind == "min_gap_y":
            if len(ns) != 2 or value is None: raise ConstraintError("min_gap_y requires two nodes and value")
            top, bottom = sorted(ns, key=lambda n: n.box.y)
            mag = max(0.0, value - (bottom.box.y - top.box.bottom))
        elif kind == "min_width":
            if len(ns) != 1 or value is None: raise ConstraintError("min_width requires one node and value")
            mag = max(0.0, value - ns[0].box.width)
        elif kind == "min_height":
            if len(ns) != 1 or value is None: raise ConstraintError("min_height requires one node and value")
            mag = max(0.0, value - ns[0].box.height)
        if mag > tolerance:
            out.append(ConstraintViolation(spec["id"], kind, spec["nodes"], float(mag), f"{kind} violated by {mag:.6f}"))
    return tuple(out)
