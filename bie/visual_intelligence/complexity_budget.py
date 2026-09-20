from __future__ import annotations
from dataclasses import dataclass

class ComplexityBudgetError(ValueError): pass

@dataclass(frozen=True)
class SceneComplexity:
    required_semantic_ids:tuple[str,...]
    element_count:int
    text_chars:int
    asset_bytes:int
    vector_ops:int
    animation_tracks:int
    three_d_objects:int
    particle_count:int
    simulation_steps:int

@dataclass(frozen=True)
class BudgetProfile:
    profile_id:str
    max_score:float
    split_score:float
    max_asset_bytes:int
    max_3d_objects:int
    max_particles:int

@dataclass(frozen=True)
class ComplexityDecision:
    score:float
    action:str
    reasons:tuple[str,...]
    preserve_required_semantic_ids:tuple[str,...]
    simplification_hints:tuple[str,...]
    review_required:bool=True
    accepted:bool=False

def estimate_complexity(scene):
    vals=(scene.element_count,scene.text_chars,scene.asset_bytes,scene.vector_ops,scene.animation_tracks,
          scene.three_d_objects,scene.particle_count,scene.simulation_steps)
    if any(isinstance(v,bool) or not isinstance(v,int) or v<0 for v in vals):
        raise ComplexityBudgetError("complexity inputs must be nonnegative integers")
    return round(
        scene.element_count*.8 + scene.text_chars/120 + scene.asset_bytes/1_000_000*2.5 +
        scene.vector_ops/80 + scene.animation_tracks*1.2 + scene.three_d_objects*5 +
        scene.particle_count/500 + scene.simulation_steps/1000, 4
    )

def evaluate_budget(scene,profile):
    score=estimate_complexity(scene); reasons=[]; hints=[]
    if scene.asset_bytes>profile.max_asset_bytes: reasons.append("asset_budget_exceeded"); hints.append("compress_or_reuse_assets")
    if scene.three_d_objects>profile.max_3d_objects: reasons.append("3d_budget_exceeded"); hints.append("reduce_3d_or_use_2d_fallback")
    if scene.particle_count>profile.max_particles: reasons.append("particle_budget_exceeded"); hints.append("reduce_particle_density")
    if score>profile.split_score:
        action="SPLIT_SCENE"; reasons.append("complexity_above_split_threshold")
    elif score>profile.max_score or reasons:
        action="SIMPLIFY"; reasons.append("complexity_above_budget" if score>profile.max_score else "resource_budget_exceeded")
    else:
        action="PASS"
    return ComplexityDecision(score,action,tuple(sorted(set(reasons))),scene.required_semantic_ids,
                              tuple(sorted(set(hints))),True,False)

def assert_semantics_preserved(decision,output_semantic_ids):
    missing=set(decision.preserve_required_semantic_ids)-set(output_semantic_ids)
    if missing: raise ComplexityBudgetError(f"required semantics lost: {sorted(missing)}")
    return True
