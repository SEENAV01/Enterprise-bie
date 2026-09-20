from dataclasses import dataclass
from .asset_contracts import *
@dataclass(frozen=True)
class AssetQualityReport:
    asset_id:str; semantic_alignment:float; legibility:float; resolution:float; provenance_quality:float
    rights_readiness:float; weighted_score:float; blockers:tuple[str,...]; review_required:bool=True
def evaluate_asset_quality(asset,*,metrics,rights_ready):
    req=("semantic_alignment","legibility","resolution","provenance_quality")
    missing=[k for k in req if k not in metrics]
    if missing: raise AssetValidationError(f"missing quality metrics: {missing}")
    s=conf(metrics["semantic_alignment"],field_name="semantic_alignment"); l=conf(metrics["legibility"],field_name="legibility")
    r=conf(metrics["resolution"],field_name="resolution"); p=conf(metrics["provenance_quality"],field_name="provenance_quality")
    rr=1. if rights_ready else 0.; score=round(.35*s+.25*l+.15*r+.15*p+.10*rr,6)
    b=[]
    if s<.70:b.append("semantic_alignment_below_floor")
    if l<.65:b.append("legibility_below_floor")
    if p<.60:b.append("provenance_quality_below_floor")
    if not rights_ready:b.append("rights_not_ready")
    return AssetQualityReport(asset.asset_id,s,l,r,p,rr,score,tuple(b),True)
def production_ready(report,*,threshold=.75):
    if not 0<=threshold<=1: raise AssetValidationError("threshold")
    return report.weighted_score>=threshold and not report.blockers
