from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable
from bie.reasoning.reasoning_integration_gate import ReasoningStageEvidence, reasoning_integration_gate
from bie.reasoning.cross_family_arbitration import FamilyConstraint, arbitrate_constraints

@dataclass(frozen=True)
class SourceAnchor:
    anchor_id: str
    page: int
    text_excerpt: str

@dataclass(frozen=True)
class RealBookReasoningFixture:
    fixture_id: str
    anchors: tuple[SourceAnchor,...]
    stage_artifacts: tuple[ReasoningStageEvidence,...]
    constraints: tuple[FamilyConstraint,...]

@dataclass(frozen=True)
class RealBookFixtureReport:
    fixture_id: str
    passed: bool
    missing_anchor_evidence_ids: tuple[str,...]
    integration_passed: bool
    arbitration_status: str

def evaluate_realbook_fixture(f:RealBookReasoningFixture) -> RealBookFixtureReport:
    if not f.fixture_id.strip() or not f.anchors: raise ValueError("fixture/anchors required")
    anchor_ids={a.anchor_id for a in f.anchors}
    if len(anchor_ids)!=len(f.anchors): raise ValueError("duplicate anchor")
    if any(a.page<1 or not a.text_excerpt.strip() for a in f.anchors): raise ValueError("invalid source anchor")
    referenced={e for a in f.stage_artifacts for e in a.evidence_ids}
    referenced |= {e for c in f.constraints for e in c.evidence_ids}
    missing=tuple(sorted(referenced-anchor_ids))
    integ=reasoning_integration_gate(f.stage_artifacts)
    arb=arbitrate_constraints(f.constraints)
    passed=not missing and integ.passed and arb.status=="RESOLVED" and not arb.requires_review
    return RealBookFixtureReport(f.fixture_id,passed,missing,integ.passed,arb.status)
