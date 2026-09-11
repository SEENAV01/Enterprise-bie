from __future__ import annotations
from dataclasses import dataclass, asdict
import hashlib, json
from typing import Iterable
from bie.reasoning.reasoning_status_semantics import REVIEW_CONFIDENCE_THRESHOLD

_STATUSES={"RESOLVED","AMBIGUOUS","CONFLICT","UNREACHABLE","ABSTAINED","INSUFFICIENT_EVIDENCE"}

@dataclass(frozen=True)
class ReasoningProvenanceEnvelope:
    artifact_id: str
    reasoning_family: str
    status: str
    evidence_ids: tuple[str,...]
    parent_artifact_ids: tuple[str,...] = ()
    assumptions: tuple[str,...] = ()
    uncertainty: tuple[str,...] = ()
    confidence: float = 1.0
    requires_review: bool = False

    def validate(self):
        if not self.artifact_id.strip() or not self.reasoning_family.strip(): raise ValueError("artifact/family required")
        if self.status not in _STATUSES: raise ValueError("unsupported status")
        if not 0 <= self.confidence <= 1: raise ValueError("confidence")
        if self.confidence < REVIEW_CONFIDENCE_THRESHOLD and not self.requires_review:
            raise ValueError("low confidence requires review")
        if self.status != "RESOLVED" and not self.requires_review: raise ValueError("non-resolved status requires review")
        if (self.uncertainty or self.status in {"AMBIGUOUS","CONFLICT"}) and not self.requires_review:
            raise ValueError("uncertainty/conflict requires review")

    def canonical_json(self):
        self.validate()
        return json.dumps(asdict(self),sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False)

    def fingerprint(self):
        return "sha256:"+hashlib.sha256(self.canonical_json().encode()).hexdigest()

def make_reasoning_envelope(*,artifact_id,reasoning_family,status,evidence_ids:Iterable[str],
                            parent_artifact_ids=(),assumptions=(),uncertainty=(),confidence=1.0,
                            requires_review=False):
    e=ReasoningProvenanceEnvelope(
        artifact_id,reasoning_family,status,tuple(sorted(set(evidence_ids))),
        tuple(sorted(set(parent_artifact_ids))),tuple(assumptions),tuple(uncertainty),
        confidence,requires_review)
    e.validate(); return e
