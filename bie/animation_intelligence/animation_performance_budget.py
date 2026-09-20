from dataclasses import dataclass

class AniPerformanceError(ValueError): pass

@dataclass(frozen=True)
class AnimationComplexity:
    required_track_ids:tuple[str,...]
    track_count:int
    max_simultaneous_tracks:int
    particle_count:int
    three_d_objects:int
    simulation_steps:int
    camera_moves:int
    asset_bytes:int

@dataclass(frozen=True)
class AnimationBudget:
    profile_id:str
    max_score:float
    split_score:float
    max_particles:int
    max_3d_objects:int
    max_asset_bytes:int

@dataclass(frozen=True)
class BudgetDecision:
    score:float
    action:str
    reasons:tuple[str,...]
    preserve_required_track_ids:tuple[str,...]
    review_required:bool=True
    accepted:bool=False

def score_complexity(c):
    vals=(c.track_count,c.max_simultaneous_tracks,c.particle_count,c.three_d_objects,
          c.simulation_steps,c.camera_moves,c.asset_bytes)
    if any(isinstance(v,bool) or not isinstance(v,int) or v<0 for v in vals):
        raise AniPerformanceError("invalid complexity value")
    return round(
        c.track_count*.7 +
        c.max_simultaneous_tracks*1.8 +
        c.particle_count/400 +
        c.three_d_objects*5 +
        c.simulation_steps/1000 +
        c.camera_moves*1.5 +
        c.asset_bytes/1_000_000*2.5, 4
    )

def evaluate_budget(c,b):
    s=score_complexity(c);reasons=[]
    if c.particle_count>b.max_particles: reasons.append("particle_budget")
    if c.three_d_objects>b.max_3d_objects: reasons.append("3d_budget")
    if c.asset_bytes>b.max_asset_bytes: reasons.append("asset_budget")
    if s>b.split_score:
        action="SPLIT_SCENE";reasons.append("complexity_split")
    elif s>b.max_score or reasons:
        action="SIMPLIFY";reasons.append("complexity_budget")
    else:
        action="PASS"
    return BudgetDecision(s,action,tuple(sorted(set(reasons))),c.required_track_ids,True,False)

def assert_required_tracks_preserved(decision,output_track_ids):
    missing=set(decision.preserve_required_track_ids)-set(output_track_ids)
    if missing:
        raise AniPerformanceError("required semantic tracks lost")
    return True
