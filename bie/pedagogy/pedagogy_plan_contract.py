from __future__ import annotations
from dataclasses import dataclass, asdict, replace
from typing import Iterable
import json, hashlib
from bie.pedagogy.pedagogy_provenance import _normalize_ids, _cycle_blocked_ids

STATUSES={"RESOLVED","AMBIGUOUS","CONFLICT","ABSTAINED","INSUFFICIENT_EVIDENCE","UNREACHABLE"}

@dataclass(frozen=True)
class PedagogyDecision:
    decision_id: str
    kind: str
    payload_id: str
    evidence_ids: tuple[str,...]
    parent_decision_ids: tuple[str,...] = ()
    status: str = "RESOLVED"
    confidence: float = 1.0
    requires_review: bool = False

    def validate(self):
        if not self.decision_id.strip() or not self.kind.strip() or not self.payload_id.strip():
            raise ValueError("decision identifiers required")
        _normalize_ids(self.evidence_ids, "decision evidence")
        _normalize_ids(self.parent_decision_ids, "decision parents", required=False)
        if type(self.requires_review) is not bool:
            raise ValueError("requires_review must be boolean")
        if self.status not in STATUSES:
            raise ValueError("unsupported status")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence")
        if self.status != "RESOLVED" and not self.requires_review:
            raise ValueError("non-resolved decision requires review")
        if self.confidence < .75 and not self.requires_review:
            raise ValueError("low-confidence decision requires review")

@dataclass(frozen=True)
class UnifiedPedagogyPlan:
    plan_id: str
    source_id: str
    objective_ids: tuple[str,...]
    lesson_ids: tuple[str,...]
    decisions: tuple[PedagogyDecision,...]
    policy_version: str
    requires_review: bool

    def canonical_json(self) -> str:
        return json.dumps(asdict(self),sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False)

    def fingerprint(self) -> str:
        return "sha256:"+hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

def build_pedagogy_plan(
    *,
    plan_id: str,
    source_id: str,
    objective_ids: Iterable[str],
    lesson_ids: Iterable[str],
    decisions: Iterable[PedagogyDecision],
    policy_version: str,
) -> UnifiedPedagogyPlan:
    if not plan_id.strip() or not source_id.strip() or not policy_version.strip():
        raise ValueError("plan/source/policy required")
    objectives=_normalize_ids(objective_ids, "objectives")
    lessons=_normalize_ids(lesson_ids, "lessons")
    ds=tuple(sorted((replace(d, evidence_ids=_normalize_ids(d.evidence_ids, "decision evidence"),
                             parent_decision_ids=_normalize_ids(d.parent_decision_ids, "decision parents", required=False))
                     for d in decisions),key=lambda d:d.decision_id))
    if not objectives or not lessons or not ds:
        raise ValueError("objectives, lessons and decisions required")
    ids=[d.decision_id for d in ds]
    if len(ids)!=len(set(ids)):
        raise ValueError("duplicate decision_id")
    known=set(ids)
    for d in ds:
        d.validate()
        if any(p not in known for p in d.parent_decision_ids):
            raise ValueError("unknown parent decision")
    if _cycle_blocked_ids({d.decision_id: d.parent_decision_ids for d in ds}):
        raise ValueError("cyclic decision lineage")
    return UnifiedPedagogyPlan(
        plan_id,source_id,objectives,lessons,ds,policy_version,
        any(d.requires_review for d in ds)
    )
