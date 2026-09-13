from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class LoadFactors:
    intrinsic: float
    prerequisite_novelty: float
    symbol_math: float
    visual_interaction: float
    narration_pace: float
    segmentation_support: float

@dataclass(frozen=True)
class LoadBudgetResult:
    score: float
    overload: bool
    recommendations: tuple[str,...]

def evaluate_load_budget(f: LoadFactors, *, threshold: float=.68) -> LoadBudgetResult:
    vals=(f.intrinsic,f.prerequisite_novelty,f.symbol_math,f.visual_interaction,f.narration_pace,f.segmentation_support)
    if any(not 0<=x<=1 for x in vals) or not 0<threshold<=1:
        raise ValueError("load inputs")
    score=(.25*f.intrinsic+.2*f.prerequisite_novelty+.2*f.symbol_math+
           .15*f.visual_interaction+.15*f.narration_pace-.15*f.segmentation_support)
    score=max(0,min(1,score))
    rec=[]
    if score>threshold:
        rec.append("split lesson or scene")
        if f.prerequisite_novelty>.6: rec.append("insert prerequisite bridge")
        if f.symbol_math>.6: rec.append("stage notation and derivation")
        if f.visual_interaction>.6: rec.append("reduce simultaneous visual/interaction elements")
        if f.narration_pace>.6: rec.append("slow narration or add pauses")
        rec.append("increase segmentation support")
    return LoadBudgetResult(score,score>threshold,tuple(rec))
