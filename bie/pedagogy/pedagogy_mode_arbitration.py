from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

MODES={"EXPLANATION","INQUIRY","DERIVATION","SIMULATION"}

@dataclass(frozen=True)
class ModeCandidate:
    mode: str
    objective_fit: float
    evidence_fit: float
    readiness_fit: float
    misconception_fit: float

@dataclass(frozen=True)
class ModeTransition:
    selected_mode: str
    previous_mode: str | None
    score: float
    transition_reason: str
    requires_review: bool

def arbitrate_mode(
    candidates: Iterable[ModeCandidate],
    *,
    previous_mode: str | None=None,
    switch_margin: float=.08,
) -> ModeTransition:
    cs=tuple(candidates)
    if not 0<=switch_margin<=1:
        raise ValueError("switch margin")
    if previous_mode is not None and previous_mode not in MODES:
        raise ValueError("previous_mode")
    if not cs:
        raise ValueError("candidates")
    scores=[]
    for c in cs:
        if c.mode not in MODES or any(not 0<=x<=1 for x in (c.objective_fit,c.evidence_fit,c.readiness_fit,c.misconception_fit)):
            raise ValueError("candidate")
        if c.evidence_fit==0:
            continue
        score=.35*c.objective_fit+.25*c.evidence_fit+.25*c.readiness_fit+.15*c.misconception_fit
        scores.append((score,c.mode))
    if not scores:
        raise ValueError("no evidence-supported mode candidates")
    scores.sort(reverse=True)
    best_score,best_mode=scores[0]
    review=(len(scores)>1 and abs(scores[0][0]-scores[1][0])<.02) or best_score<.75
    if previous_mode and previous_mode != best_mode and any(m==previous_mode for _,m in scores):
        prev_score=next((s for s,m in scores if m==previous_mode),0)
        if best_score-prev_score < switch_margin:
            return ModeTransition(previous_mode,previous_mode,prev_score,"avoid unnecessary mode churn",review or prev_score<.75)
    reason="highest governed pedagogical fit" if not review else "near-tie between modes"
    return ModeTransition(best_mode,previous_mode,best_score,reason,review)
