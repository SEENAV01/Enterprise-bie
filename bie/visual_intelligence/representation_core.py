from __future__ import annotations
from dataclasses import dataclass,field
from hashlib import sha256
from math import isfinite
from typing import Any,Mapping
import json
class RepresentationError(ValueError):pass
class RepresentationGroundingError(RepresentationError):pass
class RepresentationCapabilityError(RepresentationError):pass
REPS=('diagram','simulation','map','timeline','graph','equation','image','table','2d_model','3d_model','annotation','text')
def token(v,n):
 if not isinstance(v,str) or not v.strip():raise RepresentationError(f'{n} must be nonblank')
 return v.strip()
def ids(v,n,empty=False):
 out=tuple(token(x,n) for x in (v or ()))
 if not empty and not out:raise RepresentationGroundingError(f'{n} required')
 if len(set(out))!=len(out):raise RepresentationGroundingError(f'{n} duplicates')
 return out
def unit(v,n):
 if isinstance(v,bool) or not isinstance(v,(int,float)) or not isfinite(float(v)) or not 0<=float(v)<=1:raise RepresentationError(f'{n} must be [0,1]')
 return float(v)
def canon(v):
 if isinstance(v,Mapping):return {str(k):canon(v[k]) for k in sorted(v,key=str)}
 if isinstance(v,(list,tuple)):return [canon(x) for x in v]
 if isinstance(v,set):return sorted(canon(x) for x in v)
 if isinstance(v,float):
  if not isfinite(v):raise RepresentationError('nonfinite')
  return v
 if v is None or isinstance(v,(str,int,bool)):return v
 raise RepresentationError(type(v).__name__)
def fp(v):return sha256(json.dumps(canon(v),sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
@dataclass(frozen=True)
class TargetProfile:
 profile_id:str;capabilities:tuple[str,...];max_complexity:float=1.;supports_interaction:bool=False;supports_3d:bool=False;supports_simulation:bool=False
 def __post_init__(self):
  object.__setattr__(self,'profile_id',token(self.profile_id,'profile_id'));object.__setattr__(self,'capabilities',ids(self.capabilities,'capabilities',True));object.__setattr__(self,'max_complexity',unit(self.max_complexity,'max_complexity'))
@dataclass(frozen=True)
class SemanticIntent:
 intent_id:str;domain:str;concept_ids:tuple[str,...];evidence_refs:tuple[str,...];reasoning_refs:tuple[str,...];semantic_tags:tuple[str,...]
 dynamic:bool=False;spatial:bool=False;temporal:bool=False;quantitative:bool=False;equation_present:bool=False;interaction_value:float=0.;uncertainty:float=0.;payload:Mapping[str,Any]=field(default_factory=dict)
 def __post_init__(self):
  object.__setattr__(self,'intent_id',token(self.intent_id,'intent_id'));object.__setattr__(self,'domain',token(self.domain,'domain').lower());object.__setattr__(self,'concept_ids',ids(self.concept_ids,'concept_ids'));object.__setattr__(self,'evidence_refs',ids(self.evidence_refs,'evidence_refs'));object.__setattr__(self,'reasoning_refs',ids(self.reasoning_refs,'reasoning_refs'));object.__setattr__(self,'semantic_tags',ids(self.semantic_tags,'semantic_tags',True));object.__setattr__(self,'interaction_value',unit(self.interaction_value,'interaction_value'));object.__setattr__(self,'uncertainty',unit(self.uncertainty,'uncertainty'));object.__setattr__(self,'payload',canon(dict(self.payload)))
@dataclass(frozen=True)
class Candidate:
 candidate_id:str;representation:str;evidence_refs:tuple[str,...];reasoning_refs:tuple[str,...];capabilities:tuple[str,...];rationale:tuple[str,...];base_confidence:float;payload:Mapping[str,Any]=field(default_factory=dict)
 def __post_init__(self):
  object.__setattr__(self,'candidate_id',token(self.candidate_id,'candidate_id'));r=token(self.representation,'representation').lower();
  if r not in REPS:raise RepresentationError('unsupported representation')
  object.__setattr__(self,'representation',r);object.__setattr__(self,'evidence_refs',ids(self.evidence_refs,'evidence_refs'));object.__setattr__(self,'reasoning_refs',ids(self.reasoning_refs,'reasoning_refs'));object.__setattr__(self,'capabilities',ids(self.capabilities,'capabilities',True));object.__setattr__(self,'rationale',ids(self.rationale,'rationale',True));object.__setattr__(self,'base_confidence',unit(self.base_confidence,'base_confidence'));object.__setattr__(self,'payload',canon(dict(self.payload)))
@dataclass(frozen=True)
class Decision:
 decision_id:str;selected:str|None;status:str;confidence:float;rationale:tuple[str,...];evidence_refs:tuple[str,...];reasoning_refs:tuple[str,...];payload:Mapping[str,Any];fingerprint:str;review_required:bool=True;accepted:bool=False
def decision(intent,selected,status,confidence,rationale,payload=None,suffix='decision'):
 if status not in {'PASS','REVIEW','BLOCKED','UNSUPPORTED','ABSTAIN'}:raise RepresentationError('bad status')
 if selected is not None:selected=token(selected,'selected')
 confidence=unit(confidence,'confidence');d={'id':intent.intent_id+':'+suffix,'selected':selected,'status':status,'confidence':confidence,'rationale':tuple(rationale),'evidence':intent.evidence_refs,'reasoning':intent.reasoning_refs,'payload':canon(dict(payload or {})),'accepted':False}
 return Decision(d['id'],selected,status,confidence,tuple(rationale),intent.evidence_refs,intent.reasoning_refs,d['payload'],fp(d),True,False)
