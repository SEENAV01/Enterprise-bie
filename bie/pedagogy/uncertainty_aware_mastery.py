from dataclasses import dataclass
import json,hashlib
from bie.pedagogy.pedagogy_provenance import _normalize_ids

@dataclass(frozen=True)
class MasteryObservation:
    observation_id:str; concept_id:str; score:float; reliability:float; age_steps:int=0; evidence_ids:tuple[str,...]=()
    def validate(self):
        if not self.observation_id.strip() or not self.concept_id.strip() or not self.evidence_ids: raise ValueError("grounding")
        _normalize_ids(self.evidence_ids,"observation evidence")
        if not 0<=self.score<=1 or not 0<=self.reliability<=1 or type(self.age_steps) is not int or self.age_steps<0: raise ValueError("values")
@dataclass(frozen=True)
class KnowledgeState:
    concept_id:str; mean_mastery:float; lower_bound:float; upper_bound:float; confidence:float; evidence_ids:tuple[str,...]; observation_ids:tuple[str,...]; conflict:bool; requires_review:bool
    def fingerprint(self):
        return "sha256:"+hashlib.sha256(json.dumps(self.__dict__,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()

def infer_knowledge_state(concept_id,observations,*,recency_decay=.92,conflict_gap=.45,review_confidence_below=.65):
    if not isinstance(concept_id,str) or not concept_id.strip(): raise ValueError("concept_id")
    if not 0<recency_decay<=1 or not 0<conflict_gap<=1 or not 0<=review_confidence_below<=1:
        raise ValueError("mastery policy values")
    obs=tuple(sorted((o for o in observations if o.concept_id==concept_id),key=lambda o:o.observation_id))
    if not obs:return KnowledgeState(concept_id,.5,0,1,0,(),(),False,True)
    ids=[o.observation_id for o in obs]
    if len(ids)!=len(set(ids)):raise ValueError("duplicate observation")
    weighted=[]
    for o in obs:
        o.validate(); weighted.append((o,o.reliability*(recency_decay**o.age_steps)))
    tw=sum(w for _,w in weighted)
    if tw<=0:return KnowledgeState(concept_id,.5,0,1,0,tuple(sorted({e for o,_ in weighted for e in o.evidence_ids})),tuple(sorted(ids)),False,True)
    mean=sum(o.score*w for o,w in weighted)/tw
    var=sum(w*(o.score-mean)**2 for o,w in weighted)/tw
    agreement=max(0,1-min(1,var/.25)); support=min(1,tw/2)
    conf=.55*agreement+.45*support
    width=max(.05,(1-conf)*.5)
    scores=[o.score for o,_ in weighted if o.reliability>0]
    conflict=len(scores)>=2 and max(scores)-min(scores)>=conflict_gap
    return KnowledgeState(concept_id,mean,max(0,mean-width),min(1,mean+width),conf,tuple(sorted({e for o,_ in weighted for e in o.evidence_ids})),tuple(sorted(ids)),conflict,conflict or conf<review_confidence_below)

def combine_concept_states(states):
    states=tuple(states)
    if not states:raise ValueError("states")
    return min(s.mean_mastery for s in states),min(s.confidence for s in states),any(s.requires_review for s in states)
