from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable
import hashlib, json
from bie.pedagogy.pedagogy_provenance import _normalize_ids
from bie.pedagogy.uncertainty_aware_mastery import KnowledgeState

STATES={"BRIDGE","REMEDIATE","PRACTICE","STANDARD","ACCELERATE","MASTERY_CHECK","MASTERED"}

@dataclass(frozen=True)
class AdaptiveState:
    learner_id: str
    concept_id: str
    state: str
    mastery: float
    version: int
    evidence_ids: tuple[str,...]
    requires_review: bool = False
    mastery_confidence: float = 1.0
    observation_ids: tuple[str,...] = ()

@dataclass(frozen=True)
class AdaptiveTransition:
    from_state: str
    to_state: str
    reason: str
    evidence_ids: tuple[str,...]
    requires_review: bool = False

def next_state(
    current: AdaptiveState,
    *,
    prerequisite_ready: bool,
    misconception_detected: bool,
    transfer_passed: bool,
    new_mastery: float,
    evidence_ids: Iterable[str],
    knowledge_state: KnowledgeState | None = None,
) -> tuple[AdaptiveState,AdaptiveTransition]:
    if current.state not in STATES or not 0<=current.mastery<=1 or current.version<0:
        raise ValueError("invalid current state")
    if not 0<=new_mastery<=1:
        raise ValueError("new_mastery")
    if not current.learner_id.strip() or not current.concept_id.strip():
        raise ValueError("learner/concept identifiers required")
    if any(type(x) is not bool for x in (prerequisite_ready, misconception_detected, transfer_passed, current.requires_review)):
        raise ValueError("state gates must be booleans")
    ev=_normalize_ids(evidence_ids, "transition evidence")
    prior=_normalize_ids(current.evidence_ids, "prior evidence", required=False)
    review=current.requires_review
    confidence=current.mastery_confidence
    observations=current.observation_ids
    if not 0<=confidence<=1:
        raise ValueError("mastery confidence")
    review=review or confidence<.75
    if knowledge_state is not None:
        if not isinstance(knowledge_state, KnowledgeState) or knowledge_state.concept_id != current.concept_id:
            raise ValueError("knowledge state concept mismatch")
        if not 0<=knowledge_state.confidence<=1 or not 0<=knowledge_state.lower_bound<=knowledge_state.mean_mastery<=knowledge_state.upper_bound<=1:
            raise ValueError("invalid knowledge state bounds/confidence")
        if abs(knowledge_state.mean_mastery-new_mastery)>1e-12:
            raise ValueError("new_mastery differs from supplied knowledge state")
        confidence=knowledge_state.confidence
        review=knowledge_state.requires_review or knowledge_state.conflict or confidence<.75
        observations=_normalize_ids(knowledge_state.observation_ids, "mastery observations", required=False)
        prior+=_normalize_ids(knowledge_state.evidence_ids, "mastery evidence", required=False)
        if not knowledge_state.evidence_ids:
            review=True
    ev=tuple(sorted(set(prior+ev)))
    if not prerequisite_ready:
        target,reason="BRIDGE","prerequisites not ready"
    elif misconception_detected:
        target,reason="REMEDIATE","misconception detected"
    elif review:
        target,reason="STANDARD","mastery uncertainty requires review before advancement"
    elif new_mastery>=.9 and transfer_passed:
        target,reason="MASTERED","high mastery plus transfer"
    elif new_mastery>=.85:
        target,reason="ACCELERATE","high mastery"
    elif new_mastery>=.7:
        target,reason="MASTERY_CHECK","approaching mastery"
    elif new_mastery>=.5:
        target,reason="PRACTICE","developing mastery"
    else:
        target,reason="STANDARD","needs instruction"
    nxt=AdaptiveState(current.learner_id,current.concept_id,target,new_mastery,current.version+1,ev,review,confidence,observations)
    return nxt,AdaptiveTransition(current.state,target,reason,ev,review)

def state_fingerprint(state: AdaptiveState) -> str:
    payload=json.dumps(state.__dict__,sort_keys=True,separators=(",",":"),allow_nan=False)
    return "sha256:"+hashlib.sha256(payload.encode()).hexdigest()
