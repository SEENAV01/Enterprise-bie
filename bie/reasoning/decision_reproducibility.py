from __future__ import annotations
from dataclasses import asdict, dataclass, is_dataclass
import hashlib, json
from bie.reasoning.decision_contracts import ReasoningDecision

def _canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False)

def decision_fingerprint(decision: ReasoningDecision) -> str:
    if not isinstance(decision,ReasoningDecision): raise TypeError("decision must be ReasoningDecision")
    decision.validate()
    payload=asdict(decision)
    return "sha256:"+hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()

@dataclass(frozen=True)
class ReproducibilityReport:
    baseline_decision_id: str
    candidate_decision_id: str
    baseline_fingerprint: str
    candidate_fingerprint: str
    identical: bool
    changed_fields: tuple[str, ...]
    passed: bool
    requires_review: bool

def compare_decisions(
    baseline: ReasoningDecision,
    candidate: ReasoningDecision,
    *,
    require_same_decision_id: bool=True,
) -> ReproducibilityReport:
    if not isinstance(baseline,ReasoningDecision) or not isinstance(candidate,ReasoningDecision):
        raise TypeError("baseline and candidate must be ReasoningDecision")
    baseline.validate(); candidate.validate()
    a=asdict(baseline); b=asdict(candidate)
    changed=tuple(sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k)))
    if require_same_decision_id and baseline.decision_id != candidate.decision_id:
        changed=tuple(sorted(set(changed)|{"decision_id"}))
    fa=decision_fingerprint(baseline); fb=decision_fingerprint(candidate)
    identical=(fa==fb)
    passed=identical and (not require_same_decision_id or baseline.decision_id==candidate.decision_id)
    return ReproducibilityReport(
      baseline.decision_id,candidate.decision_id,fa,fb,identical,changed,passed,not passed)
