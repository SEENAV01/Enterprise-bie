from dataclasses import dataclass,field
from hashlib import sha256
from math import isfinite,sqrt
from typing import Mapping,Any
import json
class PhysError(ValueError):pass
class GroundingError(PhysError):pass
def tok(v,n):
    if not isinstance(v,str) or not v.strip():raise PhysError(f"{n} blank")
    return v.strip()
def finite(v,n):
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not isfinite(float(v)):raise PhysError(f"{n} invalid")
    return float(v)
def canon(v):
    if isinstance(v,Mapping):return {str(k):canon(v[k]) for k in sorted(v,key=str)}
    if isinstance(v,(tuple,list)):return [canon(x) for x in v]
    if v is None or isinstance(v,(str,int,float,bool)):return v
    raise PhysError("unsupported payload")
def fp(v):return sha256(json.dumps(canon(v),sort_keys=True,separators=(",",":")).encode()).hexdigest()
@dataclass(frozen=True)
class Context:
    intent_id:str;evidence_refs:tuple[str,...];reasoning_refs:tuple[str,...];visual_plan_fingerprint:str;frame:str
    model_fingerprint:str|None=None;uncertainty:float=0.;payload:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        object.__setattr__(self,"intent_id",tok(self.intent_id,"intent_id"))
        if not self.evidence_refs or not self.reasoning_refs:raise GroundingError("lineage required")
        f=tok(self.visual_plan_fingerprint,"visual_plan_fingerprint").lower()
        if len(f)!=64 or any(c not in "0123456789abcdef" for c in f):raise PhysError("bad visual fp")
        object.__setattr__(self,"visual_plan_fingerprint",f);object.__setattr__(self,"frame",tok(self.frame,"frame"))
        if self.model_fingerprint is not None:
            m=tok(self.model_fingerprint,"model_fingerprint").lower()
            if len(m)!=64 or any(c not in "0123456789abcdef" for c in m):raise PhysError("bad model fp")
            object.__setattr__(self,"model_fingerprint",m)
        if not 0<=float(self.uncertainty)<=1:raise PhysError("uncertainty")
        object.__setattr__(self,"payload",canon(dict(self.payload)))
@dataclass(frozen=True)
class Plan:
    plan_id:str;kind:str;status:str;ops:tuple[Mapping[str,Any],...];warnings:tuple[str,...];blockers:tuple[str,...];fingerprint:str;review_required:bool=True;accepted:bool=False
def plan(ctx,suffix,kind,status="PASS",ops=(),warnings=(),blockers=()):
    body={"id":ctx.intent_id+suffix,"kind":kind,"status":status,"ops":tuple(canon(dict(x)) for x in ops),"warnings":tuple(warnings),"blockers":tuple(blockers),"evidence":ctx.evidence_refs,"reasoning":ctx.reasoning_refs,"frame":ctx.frame,"model":ctx.model_fingerprint,"accepted":False}
    return Plan(body["id"],kind,status,body["ops"],tuple(warnings),tuple(blockers),fp(body),True,False)
