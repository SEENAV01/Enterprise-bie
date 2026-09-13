from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ExplanationPlan:
    concept_id: str
    sequence: tuple[str,...]
    evidence_ids: tuple[str,...]
    misconception_check: bool

def plan_explanation(
    concept_id: str,
    concise_definition: str,
    mechanism: str,
    example: str,
    evidence_ids,
    *,
    misconception_check: bool = True,
) -> ExplanationPlan:
    if not all(x.strip() for x in (concept_id,concise_definition,mechanism,example)) or not evidence_ids:
        raise ValueError("grounded explanation required")
    seq = (
        f"activate prior knowledge for {concept_id}",
        f"state definition: {concise_definition}",
        f"explain mechanism: {mechanism}",
        f"work example: {example}",
        "check understanding",
    )
    if misconception_check:
        seq += ("probe likely misconception",)
    return ExplanationPlan(concept_id,seq,tuple(sorted(set(evidence_ids))),misconception_check)
