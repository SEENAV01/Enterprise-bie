from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

@dataclass(frozen=True)
class CausalEdge:
    cause: str
    effect: str
    evidence_ids: tuple[str, ...] = ()
    contradicting_evidence_ids: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    confidence: float = 1.0

    def validate(self) -> None:
        if not self.cause.strip() or not self.effect.strip():
            raise ValueError("cause/effect required")
        if self.cause == self.effect:
            raise ValueError("self-causation not allowed")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be in [0,1]")

@dataclass(frozen=True)
class GroundedCausalGraph:
    nodes: tuple[str, ...]
    edges: tuple[CausalEdge, ...]
    confidence: float
    requires_review: bool

def build_grounded_causal_graph(
    nodes: Iterable[str],
    edges: Iterable[CausalEdge],
    *,
    review_threshold: float = .75
) -> GroundedCausalGraph:
    nodes=tuple(nodes); edges=tuple(edges)
    if len(nodes)!=len(set(nodes)):
        raise ValueError("duplicate node")
    known=set(nodes)
    if not 0 <= review_threshold <= 1:
        raise ValueError("review_threshold")
    for e in edges:
        e.validate()
        if e.cause not in known or e.effect not in known:
            raise ValueError("unknown causal node")
        if not e.evidence_ids:
            raise ValueError("causal edge requires supporting evidence")
    confidence=min((e.confidence for e in edges), default=1.0)
    review = confidence < review_threshold or any(
        e.contradicting_evidence_ids or e.assumptions for e in edges
    )
    return GroundedCausalGraph(
        tuple(sorted(nodes)),
        tuple(sorted(edges,key=lambda e:(e.cause,e.effect,e.evidence_ids))),
        confidence,
        review
    )
