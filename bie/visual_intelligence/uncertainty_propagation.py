from dataclasses import dataclass
from hashlib import sha256
from math import isfinite
import json
class UncertaintyError(ValueError): pass
def prob(v,n):
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not isfinite(float(v)) or not 0<=float(v)<=1: raise UncertaintyError(f'{n} must be in [0,1]')
    return float(v)
@dataclass(frozen=True)
class UncertaintyEvidence:
    evidence_id:str; confidence:float; kind:str; bounds:tuple[float,float]|None=None; conflict_group:str|None=None; source_ref:str|None=None
    def __post_init__(self):
        if not self.evidence_id or not self.kind: raise UncertaintyError('id/kind required')
        object.__setattr__(self,'confidence',prob(self.confidence,'confidence'))
        if self.bounds is not None:
            lo,hi=map(float,self.bounds)
            if not (isfinite(lo) and isfinite(hi) and lo<=hi): raise UncertaintyError('invalid bounds')
            object.__setattr__(self,'bounds',(lo,hi))
@dataclass(frozen=True)
class VisualUncertaintyState:
    claim_id:str; confidence:float; status:str; evidence_ids:tuple[str,...]; conflict_groups:tuple[str,...]; bounds:tuple[float,float]|None; disclosure_required:bool; disclosure_mode:str; abstain:bool; reasons:tuple[str,...]; fingerprint:str; review_required:bool=True; accepted:bool=False
def _fp(p): return sha256(json.dumps(p,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def propagate_uncertainty(*,claim_id,evidence,stage_confidences,confidence_floor=.70,abstain_floor=.40,conflict_penalty=.20,require_disclosure_below=.85):
    if not claim_id or not evidence: raise UncertaintyError('claim/evidence required')
    floor=prob(confidence_floor,'floor'); abst=prob(abstain_floor,'abstain'); disc=prob(require_disclosure_below,'disclosure'); pen=prob(conflict_penalty,'penalty')
    if abst>floor: raise UncertaintyError('abstain floor > review floor')
    vals=[min(e.confidence for e in evidence)]+[prob(v,k) for k,v in sorted(stage_confidences.items())]
    groups={}
    for e in evidence:
        if e.conflict_group: groups.setdefault(e.conflict_group,[]).append(e)
    conflicts=tuple(sorted(k for k,v in groups.items() if len(v)>1)); conf=max(0,min(vals)-pen*len(conflicts))
    bs=[e.bounds for e in evidence if e.bounds is not None]; bounds=(min(x[0] for x in bs),max(x[1] for x in bs)) if bs else None
    reasons=[]
    if conflicts: reasons.append('conflicting_evidence')
    if conf<floor: reasons.append('confidence_below_review_floor')
    if bounds is not None: reasons.append('bounded_uncertainty')
    ab=conf<abst; status='ABSTAIN' if ab else ('REVIEW' if conf<floor or conflicts else 'PASS'); disclosure=conf<disc or bool(conflicts) or bounds is not None
    payload={'claim':claim_id,'confidence':round(conf,6),'status':status,'conflicts':conflicts,'bounds':bounds,'disclosure':disclosure,'abstain':ab,'reasons':reasons}
    return VisualUncertaintyState(claim_id,round(conf,6),status,tuple(e.evidence_id for e in evidence),conflicts,bounds,disclosure,'explicit_uncertainty_label' if disclosure else 'none',ab,tuple(reasons),_fp(payload),True,False)
def enforce_visual_certainty(state,payload):
    if state.abstain and payload.get('render_claim',True): raise UncertaintyError('abstained claim cannot render')
    if state.disclosure_required and payload.get('asserted_certain',False): raise UncertaintyError('uncertain claim shown certain')
    if state.disclosure_required and not payload.get('uncertainty_visible',False): raise UncertaintyError('uncertainty disclosure missing')
    return True
