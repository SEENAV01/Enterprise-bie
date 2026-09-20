from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence

from .layout_contracts import LayoutNode, LayoutPlan, LayoutValidationError


class HierarchyError(LayoutValidationError):
    pass


@dataclass(frozen=True)
class HierarchyEntry:
    node_id: str
    depth: int
    rank: int
    parent_id: str | None


ROLE_WEIGHT = {
    "title": 100,
    "focus": 95,
    "primary": 90,
    "diagram": 80,
    "equation": 80,
    "secondary": 60,
    "annotation": 45,
    "caption": 35,
    "decorative": 10,
}


def build_hierarchy(plan: LayoutPlan) -> tuple[HierarchyEntry, ...]:
    node_map = {n.node_id: n for n in plan.nodes}
    def depth(n: LayoutNode) -> int:
        d, cur, seen = 0, n, set()
        while cur.parent_id is not None:
            if cur.node_id in seen:
                raise HierarchyError("hierarchy cycle")
            seen.add(cur.node_id)
            cur = node_map[cur.parent_id]
            d += 1
        return d

    entries = []
    for n in plan.nodes:
        d = depth(n)
        role_score = ROLE_WEIGHT.get(n.role, 50)
        rank = n.priority * 1000 + role_score * 10 - d
        entries.append(HierarchyEntry(n.node_id, d, rank, n.parent_id))
    entries.sort(key=lambda e: (-e.rank, e.node_id))
    return tuple(entries)


def reading_order(plan: LayoutPlan) -> tuple[str, ...]:
    hierarchy = {e.node_id: e for e in build_hierarchy(plan)}
    ordered = sorted(
        plan.nodes,
        key=lambda n: (hierarchy[n.node_id].depth, round(n.box.y, 6), round(n.box.x, 6), -n.priority, n.node_id),
    )
    return tuple(n.node_id for n in ordered)


def validate_parent_containment(plan: LayoutPlan) -> tuple[str, ...]:
    node_map = {n.node_id: n for n in plan.nodes}
    bad = []
    for n in plan.nodes:
        if n.parent_id and not node_map[n.parent_id].box.contains(n.box):
            bad.append(n.node_id)
    return tuple(sorted(bad))
