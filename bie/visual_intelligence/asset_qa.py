from __future__ import annotations
from dataclasses import dataclass
from .visual_qa_contracts import ids, score, token, AssetQAError, make_result

@dataclass(frozen=True)
class AssetItem:
    asset_id: str
    required: bool
    provenance_refs: tuple[str,...]
    semantic_score: float
    quality_score: float
    rights_ready: bool
    unresolved_uri: bool = False
    generated: bool = False
    grounding_checked: bool = False
    def __post_init__(self):
        object.__setattr__(self,"asset_id",token(self.asset_id,"asset_id"))
        object.__setattr__(self,"provenance_refs",ids(self.provenance_refs,"provenance_refs"))
        object.__setattr__(self,"semantic_score",score(self.semantic_score,"semantic_score"))
        object.__setattr__(self,"quality_score",score(self.quality_score,"quality_score"))

def evaluate_asset_qa(items, evidence_refs, reasoning_refs, semantic_floor=.70, quality_floor=.65):
    xs=tuple(items)
    if not xs: raise AssetQAError("asset QA requires assets")
    if len({x.asset_id for x in xs})!=len(xs): raise AssetQAError("duplicate asset ids")
    ev=set(evidence_refs); issues={}; blockers=[]; warnings=[]; weighted=[]
    for a in xs:
        ai=[]
        if a.required and not set(a.provenance_refs)&ev: ai.append("missing_evidence_overlap")
        if a.semantic_score<semantic_floor: ai.append("semantic_below_floor")
        if a.quality_score<quality_floor: ai.append("quality_below_floor")
        if a.required and not a.rights_ready: ai.append("rights_not_ready")
        if a.unresolved_uri: ai.append("unresolved_uri")
        if a.generated and not a.grounding_checked: ai.append("generated_not_grounding_checked")
        if ai: issues[a.asset_id]=ai
        hard={"missing_evidence_overlap","rights_not_ready","unresolved_uri","generated_not_grounding_checked"}
        if hard & set(ai): blockers.append("asset_blocker:"+a.asset_id)
        elif ai: warnings.append("asset_quality_warning:"+a.asset_id)
        weighted.append(.6*a.semantic_score+.4*a.quality_score)
    return make_result("vis-asset","asset_qa",sum(weighted)/len(weighted),blockers,warnings,evidence_refs,reasoning_refs,{"issues":issues})
