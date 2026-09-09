"""Versioned deterministic inference results using BIE's existing evidence contracts."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite
from numbers import Real

from bie.reasoning.decision_contracts import EvidenceRef, ReasoningDecision
from bie.bie_core.artifact_contracts import ArtifactEnvelope, ProducerIdentity, ProvenanceSummary


def identifier(value: str, field: str = "id") -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{field} must be a nonblank, trimmed string")
    return value


def finite(value: Real, field: str = "number") -> float:
    if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value):
        raise ValueError(f"{field} must be a finite real number")
    return float(value)


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def evidence(refs) -> tuple[EvidenceRef, ...]:
    refs = tuple(refs)
    if not refs:
        raise ValueError("Source evidence is required")
    ids = set()
    for ref in refs:
        if not isinstance(ref, EvidenceRef):
            raise ValueError("Expected BIE EvidenceRef")
        ref.validate()
        identifier(ref.artifact_id, "evidence artifact id")
        finite(ref.strength, "evidence strength")
        if ref.artifact_id in ids:
            raise ValueError("Duplicate evidence artifact id")
        ids.add(ref.artifact_id)
    return tuple(sorted(refs, key=lambda x: x.artifact_id))


def require_refs(ids, refs) -> tuple[str, ...]:
    if isinstance(ids, str):
        raise ValueError("Evidence ids must be a sequence, not a string")
    ids = tuple(ids)
    if not ids or len(ids) != len(set(ids)):
        raise ValueError("Nonempty unique evidence ids required")
    known = {x.artifact_id for x in refs}
    for value in ids:
        identifier(value, "evidence id")
        if value not in known:
            raise ValueError(f"Unresolved evidence id: {value}")
    return tuple(sorted(ids))


@dataclass(frozen=True)
class GroundedResult:
    task_id: str
    operation: str
    status: str
    inputs_json: str
    value_json: str
    evidence_refs: tuple[EvidenceRef, ...]
    assumptions: tuple[str, ...] = ()
    uncertainty: tuple[str, ...] = ()
    schema_version: str = "1.0.0"

    def __post_init__(self):
        identifier(self.task_id, "task id")
        identifier(self.operation, "operation")
        if self.status not in {"RESOLVED", "AMBIGUOUS", "CONFLICT", "UNREACHABLE"}:
            raise ValueError("Unsupported inference status")
        if self.schema_version != "1.0.0":
            raise ValueError("Unsupported inference schema")
        object.__setattr__(self, "evidence_refs", evidence(self.evidence_refs))
        for name in ("inputs_json", "value_json"):
            if not isinstance(json.loads(getattr(self, name)), dict):
                raise ValueError("Inference inputs and value must be JSON objects")
            if canonical(json.loads(getattr(self, name))) != getattr(self, name):
                raise ValueError("Inference JSON must be canonical and finite")
        for name in ("assumptions", "uncertainty"):
            values = tuple(getattr(self, name))
            for value in values:
                identifier(value, name)
            object.__setattr__(self, name, values)

    @property
    def value(self):
        return json.loads(self.value_json)

    @property
    def confidence(self):
        """Conservative evidence strength; not a calibrated probability of truth."""
        return min(x.strength for x in self.evidence_refs)

    @property
    def requires_review(self):
        return self.status != "RESOLVED" or self.confidence < 0.75 or bool(self.uncertainty) or any(x.role == "contradicting" for x in self.evidence_refs)

    @property
    def result_id(self):
        return "reasoning.inference:" + self.schema_version + ":" + sha256(canonical(asdict(self)).encode()).hexdigest()

    def to_dict(self):
        return {"result_id": self.result_id, "schema_version": self.schema_version, "task_id": self.task_id, "operation": self.operation, "status": self.status, "inputs": json.loads(self.inputs_json), "value": self.value, "evidence_refs": [asdict(x) for x in self.evidence_refs], "assumptions": list(self.assumptions), "uncertainty": list(self.uncertainty), "confidence": self.confidence, "requires_review": self.requires_review}

    def to_decision(self, *, decision_type: str, subject_id: str, question: str) -> ReasoningDecision:
        """The downstream caller supplies its existing decision taxonomy explicitly."""
        identifier(subject_id, "subject id")
        identifier(question, "question")
        result = ReasoningDecision(decision_id=self.result_id, decision_type=decision_type, subject_id=subject_id, question=question, selected_option=self.value_json, rationale_summary=f"{self.operation}: {self.status}. Evidence-grounded deterministic analysis.", confidence=self.confidence, evidence_refs=list(self.evidence_refs), constraints=list(self.assumptions), uncertainty=list(self.uncertainty), requires_review=self.requires_review, policy_tags=[self.task_id, "deterministic_inference"])
        result.validate(critical=True)
        return result

    def to_artifact(self, *, run_id: str, parents: tuple[ArtifactEnvelope, ...]) -> ArtifactEnvelope:
        by_id = {x.artifact_id: x for x in parents}
        if len(by_id) != len(parents):
            raise ValueError("Duplicate parent artifact")
        for parent in parents:
            parent.validate()
        required = {x.artifact_id for x in self.evidence_refs}
        if not required <= by_id.keys():
            raise ValueError("Every evidence reference must resolve to a supplied parent artifact")
        selected = [by_id[k] for k in sorted(required)]
        sources = [s for p in selected for s in p.provenance_summary.sources]
        if not sources:
            raise ValueError("Source locators are required for inference lineage")
        result = ArtifactEnvelope.create("reasoning.inference", self.schema_version, run_id, ProducerIdentity("bie.reasoning", "1.0.0", "deterministic", tool=self.operation), [p.to_ref() for p in selected], ProvenanceSummary(sources=sources, inferred=True, inference_reason=f"{self.task_id}: {self.operation}", confidence=self.confidence), {"task_id": self.task_id, "requires_review": self.requires_review}, self.to_dict())
        result.validate()
        return result


def inference(task_id, operation, inputs, value, refs, *, status="RESOLVED", assumptions=(), uncertainty=()):
    return GroundedResult(task_id, operation, status, canonical(inputs), canonical(value), evidence(refs), tuple(assumptions), tuple(uncertainty))
