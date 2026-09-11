from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Mapping
import hashlib, json
from collections import deque

@dataclass(frozen=True)
class ReasoningStageEvidence:
    stage: str
    artifact_id: str
    evidence_ids: tuple[str,...] = ()
    parent_artifact_ids: tuple[str,...] = ()
    requires_review: bool = False

@dataclass(frozen=True)
class ReasoningIntegrationReport:
    passed: bool
    missing_required_stages: tuple[str,...]
    dangling_parent_ids: tuple[str,...]
    ungrounded_stage_artifacts: tuple[str,...]
    review_artifacts: tuple[str,...]
    fingerprint: str
    cycle_blocked_artifact_ids: tuple[str,...] = ()

_REQUIRED=("evidence","decision","graph","uncertainty","qa")

def reasoning_integration_gate(
    artifacts: Iterable[ReasoningStageEvidence],
    *,
    required_stages: Iterable[str] = _REQUIRED,
) -> ReasoningIntegrationReport:
    artifacts=tuple(artifacts)
    ids=[a.artifact_id for a in artifacts]
    if len(ids)!=len(set(ids)):
        raise ValueError("duplicate artifact_id")
    required=tuple(required_stages)
    present={a.stage for a in artifacts}
    missing=tuple(sorted(set(required)-present))
    known=set(ids)
    dangling=tuple(sorted({
        p for a in artifacts for p in a.parent_artifact_ids if p not in known
    }))
    # Evidence-stage artifacts are roots and may legitimately have no evidence_ids.
    ungrounded=tuple(sorted(
        a.artifact_id for a in artifacts
        if a.stage != "evidence" and not a.evidence_ids
    ))
    reviews=tuple(sorted(a.artifact_id for a in artifacts if a.requires_review))
    # A set of present parent IDs is insufficient: derived lineage must be acyclic.
    adjacency = {artifact_id: set() for artifact_id in known}
    indegree = {artifact_id: 0 for artifact_id in known}
    for artifact in artifacts:
        for parent in set(artifact.parent_artifact_ids) & known:
            adjacency[parent].add(artifact.artifact_id)
            indegree[artifact.artifact_id] += 1
    ready = deque(sorted(k for k, degree in indegree.items() if degree == 0))
    while ready:
        for child in sorted(adjacency[ready.popleft()]):
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
    cycle_blocked = tuple(sorted(k for k, degree in indegree.items() if degree > 0))
    payload=[{
        "stage":a.stage,
        "artifact_id":a.artifact_id,
        "evidence_ids":sorted(a.evidence_ids),
        "parent_artifact_ids":sorted(a.parent_artifact_ids),
        "requires_review":a.requires_review
    } for a in sorted(artifacts,key=lambda x:(x.stage,x.artifact_id))]
    fingerprint="sha256:"+hashlib.sha256(
        json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    passed=not missing and not dangling and not ungrounded and not reviews and not cycle_blocked
    return ReasoningIntegrationReport(passed,missing,dangling,ungrounded,reviews,fingerprint,cycle_blocked)
