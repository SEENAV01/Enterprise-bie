from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Set
import hashlib
import json
import re


class ReasoningContractError(ValueError):
    pass


ALLOWED_DECISION_TYPES: Set[str] = {
    "prerequisite_order",
    "teaching_order",
    "causal_explanation",
    "mathematical_derivation",
    "misconception_resolution",
    "representation_selection",
    "example_selection",
    "assessment_strategy",
    "remediation_strategy",
    "visual_strategy",
    "simulation_strategy",
    "animation_strategy",
    "game_revision_strategy",
    "evidence_arbitration",
    "contradiction_resolution",
    "uncertainty_resolution",
}


@dataclass(frozen=True)
class EvidenceRef:
    artifact_id: str
    role: str
    strength: float
    note: Optional[str] = None

    def validate(self) -> None:
        if not self.artifact_id:
            raise ReasoningContractError("evidence artifact_id is required")
        if self.role not in {
            "primary",
            "supporting",
            "contradicting",
            "prerequisite",
            "example",
            "constraint",
            "derived",
        }:
            raise ReasoningContractError(f"invalid evidence role: {self.role}")
        if not 0.0 <= self.strength <= 1.0:
            raise ReasoningContractError("evidence strength must be in [0,1]")


@dataclass(frozen=True)
class DecisionAlternative:
    option_id: str
    description: str
    score: Optional[float] = None
    rejected_reason: Optional[str] = None

    def validate(self) -> None:
        if not self.option_id or not self.description:
            raise ReasoningContractError("alternative id and description are required")
        if self.score is not None and not 0.0 <= self.score <= 1.0:
            raise ReasoningContractError("alternative score must be in [0,1]")


@dataclass(frozen=True)
class ReasoningDecision:
    decision_id: str
    decision_type: str
    subject_id: str
    question: str
    selected_option: str
    rationale_summary: str
    confidence: float
    evidence_refs: List[EvidenceRef] = field(default_factory=list)
    alternatives: List[DecisionAlternative] = field(default_factory=list)
    premises: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    uncertainty: List[str] = field(default_factory=list)
    downstream_effects: List[str] = field(default_factory=list)
    depends_on_decisions: List[str] = field(default_factory=list)
    requires_review: bool = False
    policy_tags: List[str] = field(default_factory=list)

    def validate(
        self,
        critical: bool = False,
        critical_review_threshold: float = 0.75,
        minimum_auto_production_confidence: float = 0.50,
    ) -> None:
        if not self.decision_id:
            raise ReasoningContractError("decision_id is required")
        if self.decision_type not in ALLOWED_DECISION_TYPES:
            raise ReasoningContractError(f"unsupported decision_type: {self.decision_type}")
        if not self.subject_id or not self.question or not self.selected_option:
            raise ReasoningContractError("subject/question/selected_option are required")
        if not self.rationale_summary.strip():
            raise ReasoningContractError("rationale_summary is required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ReasoningContractError("confidence must be in [0,1]")
        for e in self.evidence_refs:
            e.validate()
        for a in self.alternatives:
            a.validate()
        if not self.evidence_refs:
            raise ReasoningContractError("reasoning decision requires evidence_refs")
        if critical and self.confidence < critical_review_threshold and not self.requires_review:
            raise ReasoningContractError(
                "critical low-confidence decision must require review/escalation"
            )
        if self.confidence < minimum_auto_production_confidence and not self.requires_review:
            raise ReasoningContractError(
                "decision below automatic production confidence must require review"
            )
        if self.decision_id in self.depends_on_decisions:
            raise ReasoningContractError("decision cannot depend on itself")


class ReasoningDecisionGraph:
    def __init__(self, decisions: List[ReasoningDecision]):
        self.by_id = {d.decision_id: d for d in decisions}
        if len(self.by_id) != len(decisions):
            raise ReasoningContractError("duplicate decision_id")

    def validate(self) -> None:
        for d in self.by_id.values():
            d.validate()
            for parent in d.depends_on_decisions:
                if parent not in self.by_id:
                    raise ReasoningContractError(
                        f"missing dependency decision {parent} for {d.decision_id}"
                    )
        self._assert_acyclic()

    def _assert_acyclic(self) -> None:
        visiting, visited = set(), set()

        def dfs(decision_id: str):
            if decision_id in visiting:
                raise ReasoningContractError("cyclic reasoning dependency detected")
            if decision_id in visited:
                return
            visiting.add(decision_id)
            for parent in self.by_id[decision_id].depends_on_decisions:
                dfs(parent)
            visiting.remove(decision_id)
            visited.add(decision_id)

        for did in self.by_id:
            dfs(did)

    def ancestors(self, decision_id: str) -> List[ReasoningDecision]:
        if decision_id not in self.by_id:
            raise ReasoningContractError("decision not found")
        out, seen = [], set()

        def walk(did: str):
            for parent in self.by_id[did].depends_on_decisions:
                if parent not in seen:
                    seen.add(parent)
                    walk(parent)
                    out.append(self.by_id[parent])

        walk(decision_id)
        return out


def decision_payload(decision: ReasoningDecision) -> Dict[str, Any]:
    decision.validate()
    return asdict(decision)
