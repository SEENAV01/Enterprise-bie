from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable
from collections import deque


def _normalize_ids(values, label, *, required=True):
    """Materialize identifiers once; a blank value is not evidence."""
    if isinstance(values, (str, bytes)):
        raise ValueError(label + " must be an iterable of identifiers")
    values = tuple(values)
    if any(not isinstance(x, str) or not x.strip() for x in values):
        raise ValueError(label + " contains blank or invalid identifiers")
    result = tuple(sorted(set(values)))
    if required and not result:
        raise ValueError(label + " required")
    return result


def _cycle_blocked_ids(parents):
    """Return cyclic nodes and their blocked descendants without recursion."""
    known = set(parents)
    indegree = {key: 0 for key in parents}
    children = {key: set() for key in parents}
    for child, incoming in parents.items():
        for parent in set(incoming) & known:
            children[parent].add(child)
            indegree[child] += 1
    ready = deque(sorted(key for key in known if indegree[key] == 0))
    while ready:
        for child in sorted(children[ready.popleft()]):
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
    return tuple(sorted(key for key in known if indegree[key]))

@dataclass(frozen=True)
class PedagogyLineage:
    artifact_id: str
    source_evidence_ids: tuple[str,...]
    reasoning_parent_ids: tuple[str,...]
    prerequisite_parent_ids: tuple[str,...] = ()
    math_parent_ids: tuple[str,...] = ()
    assumptions: tuple[str,...] = ()
    confidence: float = 1.0
    requires_review: bool = False

def build_lineage(
    artifact_id: str,
    *,
    source_evidence_ids: Iterable[str],
    reasoning_parent_ids: Iterable[str],
    prerequisite_parent_ids: Iterable[str]=(),
    math_parent_ids: Iterable[str]=(),
    assumptions: Iterable[str]=(),
    confidence: float=1.0,
    requires_review: bool=False,
) -> PedagogyLineage:
    if not artifact_id.strip():
        raise ValueError("artifact_id")
    ev=_normalize_ids(source_evidence_ids, "source evidence")
    re=_normalize_ids(reasoning_parent_ids, "reasoning lineage")
    pr=_normalize_ids(prerequisite_parent_ids, "prerequisite lineage", required=False)
    math=_normalize_ids(math_parent_ids, "math lineage", required=False)
    if not 0<=confidence<=1:
        raise ValueError("confidence")
    if type(requires_review) is not bool:
        raise ValueError("requires_review must be boolean")
    assumptions=tuple(a for a in assumptions if str(a).strip())
    if (confidence<.75 or assumptions) and not requires_review:
        raise ValueError("uncertain lineage requires review")
    return PedagogyLineage(
        artifact_id,ev,re,pr,math,assumptions,confidence,requires_review
    )

def validate_lineage_graph(lineages: Iterable[PedagogyLineage]) -> tuple[str,...]:
    ls=tuple(build_lineage(x.artifact_id, source_evidence_ids=x.source_evidence_ids,
                          reasoning_parent_ids=x.reasoning_parent_ids,
                          prerequisite_parent_ids=x.prerequisite_parent_ids,
                          math_parent_ids=x.math_parent_ids, assumptions=x.assumptions,
                          confidence=x.confidence, requires_review=x.requires_review)
             for x in lineages)
    ids={x.artifact_id for x in ls}
    if len(ids)!=len(ls):
        raise ValueError("duplicate artifact_id")
    # Parent IDs may be external upstream IDs, but internal cycles are forbidden.
    return _cycle_blocked_ids({x.artifact_id: x.reasoning_parent_ids + x.prerequisite_parent_ids + x.math_parent_ids
                               for x in ls})
