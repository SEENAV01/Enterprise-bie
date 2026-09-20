from dataclasses import dataclass
from math import isfinite

class DataAnimationError(ValueError): pass

@dataclass(frozen=True)
class DataSeries:
    series_id:str
    points:tuple[tuple[float,float],...]
    source_refs:tuple[str,...]
    uncertainty:tuple[tuple[float,float],...]|None=None

@dataclass(frozen=True)
class DataAnimationPlan:
    plan_id:str
    status:str
    operations:tuple[dict,...]
    blockers:tuple[str,...]
    warnings:tuple[str,...]
    review_required:bool=True
    accepted:bool=False

def _valid_points(points):
    return len(points)>=2 and all(
        len(p)==2 and all(isinstance(v,(int,float)) and not isinstance(v,bool) and isfinite(float(v)) for v in p)
        for p in points
    )

def plan_series_transition(plan_id,source,target,*,transition_kind="morph",
                           preserve_uncertainty=True,claim="descriptive"):
    if not _valid_points(source.points) or not _valid_points(target.points):
        raise DataAnimationError("invalid data points")
    if not source.source_refs or not target.source_refs:
        raise DataAnimationError("data lineage required")
    if transition_kind not in {"morph","crossfade","progressive","small_multiples"}:
        raise DataAnimationError("unsupported transition")
    blockers=[];warnings=[]
    if source.series_id!=target.series_id and transition_kind=="morph":
        blockers.append("morph_requires_same_series_identity")
    if (source.uncertainty or target.uncertainty) and not preserve_uncertainty:
        blockers.append("uncertainty_cannot_be_dropped")
    if claim=="causal":
        warnings.append("causal_claim_requires_external_causal_evidence")
    ops=(
      {"op":"draw_series","series_id":source.series_id,"points":source.points,"uncertainty":source.uncertainty},
      {"op":"transition_series","kind":transition_kind,"target_points":target.points,
       "target_uncertainty":target.uncertainty,"preserve_uncertainty":bool(preserve_uncertainty),"claim":claim}
    )
    return DataAnimationPlan(plan_id,"BLOCKED" if blockers else ("REVIEW" if warnings else "PASS"),
                             ops,tuple(sorted(set(blockers))),tuple(sorted(set(warnings))),True,False)

def plan_distribution_reveal(plan_id,bins,*,source_refs,normalized=False):
    bins=tuple(bins)
    if not bins or not source_refs: raise DataAnimationError("bins/source_refs required")
    if any(float(b["value"])<0 for b in bins): raise DataAnimationError("negative bin value")
    total=sum(float(b["value"]) for b in bins)
    warnings=[]
    if normalized and abs(total-1.0)>1e-6:
        warnings.append("declared_normalized_distribution_does_not_sum_to_one")
    return DataAnimationPlan(plan_id,"REVIEW" if warnings else "PASS",
                             ({"op":"reveal_distribution","bins":bins,"normalized":normalized},),
                             (),tuple(warnings),True,False)
