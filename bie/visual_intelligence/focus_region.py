from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence

from .layout_contracts import Box, LayoutNode, LayoutPlan, LayoutValidationError, finite


class FocusRegionError(LayoutValidationError):
    pass


FOCUS_ROLE_BONUS = {"focus": 100, "primary": 60, "equation": 45, "diagram": 45, "title": 30, "secondary": 10}


@dataclass(frozen=True)
class FocusDecision:
    node_id: str
    region: Box
    score: int
    rationale: tuple[str, ...]
    review_required: bool = True


def choose_focus(plan: LayoutPlan, *, preferred_ids: Sequence[str] = (), margin: float = 0.03) -> FocusDecision:
    m = finite(margin, field_name="margin")
    if m < 0 or m > 0.25:
        raise FocusRegionError("margin must be in [0,0.25]")
    preferred = set(preferred_ids)
    unknown = preferred - {n.node_id for n in plan.nodes}
    if unknown:
        raise FocusRegionError(f"unknown preferred ids: {sorted(unknown)}")
    scored = []
    for n in plan.nodes:
        score = n.priority * 10 + FOCUS_ROLE_BONUS.get(n.role, 0) + (1000 if n.node_id in preferred else 0)
        if not n.required:
            score -= 100
        scored.append((score, n.node_id, n))
    scored.sort(key=lambda x: (-x[0], x[1]))
    score, _, node = scored[0]
    rationale = [f"priority={node.priority}", f"role={node.role}"]
    if node.node_id in preferred:
        rationale.append("preferred")
    return FocusDecision(node.node_id, node.box.expand(m), score, tuple(rationale), True)


def focus_conflicts(plan: LayoutPlan, decision: FocusDecision, *, max_competing_priority: int = 85) -> tuple[str, ...]:
    focus_node = next(n for n in plan.nodes if n.node_id == decision.node_id)
    out = []
    for n in plan.nodes:
        if n.node_id == focus_node.node_id:
            continue
        if n.priority >= max_competing_priority and n.box.overlaps(decision.region):
            out.append(n.node_id)
    return tuple(sorted(out))
