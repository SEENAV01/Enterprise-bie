from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class InquiryPlan:
    phenomenon: str
    prediction_prompt: str
    evidence_prompt: str
    reflection_prompt: str
    evidence_ids: tuple[str,...]

def plan_inquiry(
    phenomenon: str,
    target_concept: str,
    evidence_ids,
    *,
    prediction_prompt: str | None = None,
) -> InquiryPlan:
    if not phenomenon.strip() or not target_concept.strip() or not evidence_ids:
        raise ValueError("grounded inquiry input required")
    prediction = prediction_prompt or f"Predict what will happen in: {phenomenon}"
    return InquiryPlan(
        phenomenon,
        prediction,
        f"What evidence from the phenomenon supports or challenges your prediction about {target_concept}?",
        f"Revise your explanation of {target_concept} using the observed evidence.",
        tuple(sorted(set(evidence_ids))),
    )
