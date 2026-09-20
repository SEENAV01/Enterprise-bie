from dataclasses import dataclass
from .asset_contracts import *
@dataclass(frozen=True)
class ReuseScore:
    asset_id:str; score:float; reasons:tuple[str,...]
def score_source_asset(need,asset):
    if asset.source_kind not in {"source","book","document"}: return ReuseScore(asset.asset_id,0.0,("not_source_asset",))
    score=0.; reasons=[]
    if asset.media_kind in need.media_kinds: score+=.40; reasons.append("media_match")
    if set(need.semantic_role.replace("-"," ").split()) & set(" ".join(asset.semantic_tags).replace("-"," ").split()):
        score+=.25; reasons.append("semantic_tag_match")
    if set(asset.provenance_refs)&set(need.evidence_refs): score+=.25; reasons.append("source_evidence_overlap")
    score+=.10*asset.quality_score
    return ReuseScore(asset.asset_id,min(1.,score),tuple(reasons))
def choose_source_reuse(need,candidates,*,threshold=.65):
    scored=[score_source_asset(need,c) for c in candidates]
    if not scored: return decision(need,"reuse_unavailable",rationale=("no_source_candidates",))
    scored.sort(key=lambda x:(-x.score,x.asset_id)); best=scored[0]
    if best.score<threshold: return decision(need,"reuse_unavailable",rationale=(f"best_score={best.score:.3f}",))
    asset=next(c for c in candidates if c.asset_id==best.asset_id)
    if not set(asset.provenance_refs)&set(need.evidence_refs): raise AssetGroundingError("no evidence overlap")
    return decision(need,"reuse_source_asset",selected=best.asset_id,rationale=best.reasons+(f"score={best.score:.3f}",))
