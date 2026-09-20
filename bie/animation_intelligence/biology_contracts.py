from dataclasses import dataclass,field
from hashlib import sha256
from math import isfinite
from typing import Mapping,Any
import json
class BioError(ValueError):pass
class BioGroundingError(BioError):pass
class BioTopologyError(BioError):pass
def tok(v,n):
    if not isinstance(v,str) or not v.strip():raise BioError(f"{n} blank")
    return v.strip()
def finite(v,n):
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not isfinite(float(v)):raise BioError(f"{n} invalid")
    return float(v)
def canon(v):
    if isinstance(v,Mapping):return {str(k):canon(v[k]) for k in sorted(v,key=str)}
    if isinstance(v,(tuple,list)):return [canon(x) for x in v]
    if v is None or isinstance(v,(str,int,float,bool)):return v
    raise BioError("unsupported payload")
def fp(v):return sha256(json.dumps(canon(v),sort_keys=True,separators=(",",":")).encode()).hexdigest()
@dataclass(frozen=True)
class Context:
    intent_id:str;evidence_refs:tuple[str,...];reasoning_refs:tuple[str,...];visual_plan_fingerprint:str;scale_level:str
    model_fingerprint:str|None=None;uncertainty:float=0.;payload:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        object.__setattr__(self,"intent_id",tok(self.intent_id,"intent_id"))
        if not self.evidence_refs or not self.reasoning_refs:raise BioGroundingError("lineage required")
        f=tok(self.visual_plan_fingerprint,"visual fp").lower()
        if len(f)!=64 or any(c not in "0123456789abcdef" for c in f):raise BioError("bad visual fp")
        object.__setattr__(self,"visual_plan_fingerprint",f);object.__setattr__(self,"scale_level",tok(self.scale_level,"scale"))
        if self.model_fingerprint is not None:
            m=tok(self.model_fingerprint,"model fp").lower()
            if len(m)!=64 or any(c not in "0123456789abcdef" for c in m):raise BioError("bad model fp")
            object.__setattr__(self,"model_fingerprint",m)
        if not 0<=float(self.uncertainty)<=1:raise BioError("uncertainty")
        object.__setattr__(self,"payload",canon(dict(self.payload)))
@dataclass(frozen=True)
class Plan:
    plan_id:str;kind:str;status:str;ops:tuple[Mapping[str,Any],...];warnings:tuple[str,...];blockers:tuple[str,...];fingerprint:str;review_required:bool=True;accepted:bool=False
def plan(ctx,suffix,kind,status="PASS",ops=(),warnings=(),blockers=()):
    body={"id":ctx.intent_id+suffix,"kind":kind,"status":status,"ops":tuple(canon(dict(x)) for x in ops),"warnings":tuple(warnings),"blockers":tuple(blockers),"evidence":ctx.evidence_refs,"reasoning":ctx.reasoning_refs,"scale":ctx.scale_level,"accepted":False}
    return Plan(body["id"],kind,status,body["ops"],tuple(warnings),tuple(blockers),fp(body),True,False)
