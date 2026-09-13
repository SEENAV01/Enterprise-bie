from __future__ import annotations
from dataclasses import dataclass, replace
from typing import Iterable
from bie.pedagogy.pedagogy_provenance import _normalize_ids, _cycle_blocked_ids

@dataclass(frozen=True)
class SourceAnchor:
    anchor_id: str
    page: int
    excerpt: str

@dataclass(frozen=True)
class PedagogyArtifactRef:
    artifact_id: str
    stage: str
    evidence_ids: tuple[str,...]
    parent_ids: tuple[str,...]=()

@dataclass(frozen=True)
class RealBookPedagogyReport:
    fixture_id: str
    missing_stages: tuple[str,...]
    missing_anchor_ids: tuple[str,...]
    dangling_parent_ids: tuple[str,...]
    passed: bool
    ungrounded_artifact_ids: tuple[str,...] = ()
    cycle_blocked_artifact_ids: tuple[str,...] = ()

REQUIRED_STAGES=("objective","sequence","bridge","example","assessment","adaptation","narrative","qa")

def evaluate_pedagogy_fixture(
    fixture_id: str,
    anchors: Iterable[SourceAnchor],
    artifacts: Iterable[PedagogyArtifactRef],
) -> RealBookPedagogyReport:
    if not fixture_id.strip():
        raise ValueError("fixture_id")
    anchors=tuple(anchors)
    artifacts=tuple(replace(a, evidence_ids=_normalize_ids(a.evidence_ids,"artifact evidence",required=False),
                            parent_ids=_normalize_ids(a.parent_ids,"artifact parents",required=False)) for a in artifacts)
    if not anchors or not artifacts:
        raise ValueError("anchors/artifacts required")
    anchor_ids={a.anchor_id for a in anchors}
    if len(anchor_ids)!=len(anchors) or any(not a.anchor_id.strip() or type(a.page) is not int or a.page<1 or not a.excerpt.strip() for a in anchors):
        raise ValueError("invalid anchors")
    ids={a.artifact_id for a in artifacts}
    if len(ids)!=len(artifacts):
        raise ValueError("duplicate artifact")
    if any(not a.artifact_id.strip() or not a.stage.strip() for a in artifacts):
        raise ValueError("artifact identifiers required")
    stages={a.stage for a in artifacts}
    missing_stages=tuple(sorted(set(REQUIRED_STAGES)-stages))
    referenced={e for a in artifacts for e in a.evidence_ids}
    missing_anchor_ids=tuple(sorted(referenced-anchor_ids))
    dangling=tuple(sorted({p for a in artifacts for p in a.parent_ids if p not in ids}))
    ungrounded=tuple(sorted(a.artifact_id for a in artifacts if not a.evidence_ids))
    cycle_blocked=_cycle_blocked_ids({a.artifact_id:a.parent_ids for a in artifacts})
    passed=not missing_stages and not missing_anchor_ids and not dangling and not ungrounded and not cycle_blocked
    return RealBookPedagogyReport(fixture_id,missing_stages,missing_anchor_ids,dangling,passed,ungrounded,cycle_blocked)
