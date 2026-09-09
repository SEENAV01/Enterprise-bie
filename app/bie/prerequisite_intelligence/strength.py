from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class StrengthSignals:
    explicit: float = 0.0
    semantic: float = 0.0
    assessment_dependency: float = 0.0
    source_order: float = 0.0
    contradiction: float = 0.0

@dataclass(frozen=True)
class StrengthScore:
    score: float
    band: str

def score_prerequisite_strength(s: StrengthSignals) -> StrengthScore:
    vals=[s.explicit,s.semantic,s.assessment_dependency,s.source_order,s.contradiction]
    if any(v<0 or v>1 for v in vals): raise ValueError("all signals must be in [0,1]")
    raw=.40*s.explicit+.25*s.semantic+.20*s.assessment_dependency+.15*s.source_order-.35*s.contradiction
    score=round(max(0.0,min(1.0,raw)),6)
    band="strong" if score>=.7 else ("moderate" if score>=.4 else "weak")
    return StrengthScore(score,band)
