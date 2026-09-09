from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

@dataclass(frozen=True)
class Concept:
    id: str
    order: int
    terms: frozenset[str] = frozenset()
    references: frozenset[str] = frozenset()

@dataclass(frozen=True)
class CandidateEdge:
    prerequisite_id: str
    dependent_id: str
    score: float
    signals: tuple[str, ...]

def generate_candidate_edges(concepts: Sequence[Concept], explicit_links: Mapping[str, Iterable[str]] | None = None,
                             threshold: float = 0.20) -> list[CandidateEdge]:
    """Generate conservative prerequisite candidates from explicit references, term overlap and source order."""
    explicit_links = explicit_links or {}
    by_id = {c.id: c for c in concepts}
    if len(by_id) != len(concepts):
        raise ValueError("concept ids must be unique")
    edges: dict[tuple[str,str], CandidateEdge] = {}
    for dep in concepts:
        prereq_ids = set(explicit_links.get(dep.id, ())) | set(dep.references)
        for pid in prereq_ids:
            if pid == dep.id or pid not in by_id:
                continue
            edges[(pid, dep.id)] = CandidateEdge(pid, dep.id, 1.0, ("explicit_reference",))
        for pre in concepts:
            if pre.id == dep.id or pre.order >= dep.order:
                continue
            overlap = len(pre.terms & dep.terms)
            union = len(pre.terms | dep.terms)
            lexical = overlap / union if union else 0.0
            distance = dep.order - pre.order
            proximity = 1.0 / (1.0 + distance)
            score = round(0.65 * lexical + 0.35 * proximity, 6)
            if score >= threshold and (pre.id, dep.id) not in edges:
                signals = tuple(s for s,v in (("term_overlap", lexical),("source_order", proximity)) if v > 0)
                edges[(pre.id, dep.id)] = CandidateEdge(pre.id, dep.id, score, signals)
    return sorted(edges.values(), key=lambda e: (-e.score, e.prerequisite_id, e.dependent_id))
