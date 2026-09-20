from dataclasses import dataclass,field
from hashlib import sha256
from math import isfinite
from typing import Mapping,Any
import json
class TimeError(ValueError):pass
class TimeGroundingError(TimeError):pass
class TimeOrderError(TimeError):pass
def tok(v,n):
    if not isinstance(v,str) or not v.strip(): raise TimeError(f"{n} blank")
    return v.strip()
def finite(v,n):
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not isfinite(float(v)): raise TimeError(f"{n} invalid")
    return float(v)
def canon(v):
    if isinstance(v,Mapping): return {str(k):canon(v[k]) for k in sorted(v,key=str)}
    if isinstance(v,(tuple,list)): return [canon(x) for x in v]
    if v is None or isinstance(v,(str,int,float,bool)): return v
    raise TimeError("unsupported payload")
def fp(v): return sha256(json.dumps(canon(v),sort_keys=True,separators=(",",":")).encode()).hexdigest()
@dataclass(frozen=True)
class Context:
    intent_id:str;evidence_refs:tuple[str,...];reasoning_refs:tuple[str,...];visual_plan_fingerprint:str;source_revision:int
    uncertainty:float=0.;payload:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        object.__setattr__(self,"intent_id",tok(self.intent_id,"intent_id"))
        if not self.evidence_refs or not self.reasoning_refs:raise TimeGroundingError("lineage required")
        f=tok(self.visual_plan_fingerprint,"visual fp").lower()
        if len(f)!=64 or any(c not in "0123456789abcdef" for c in f):raise TimeError("bad visual fp")
        object.__setattr__(self,"visual_plan_fingerprint",f)
        if self.source_revision<1:raise TimeError("bad revision")
        if not 0<=float(self.uncertainty)<=1:raise TimeError("bad uncertainty")
        object.__setattr__(self,"payload",canon(dict(self.payload)))
@dataclass(frozen=True)
class Event:
    event_id:str;label:str;source_ref:str;order_index:int|None=None;time_value:float|None=None;uncertain:bool=False;simultaneous_group:str|None=None
    def __post_init__(self):
        object.__setattr__(self,"event_id",tok(self.event_id,"event_id"));object.__setattr__(self,"label",tok(self.label,"label"));object.__setattr__(self,"source_ref",tok(self.source_ref,"source_ref"))
        if self.order_index is not None and (isinstance(self.order_index,bool) or not isinstance(self.order_index,int) or self.order_index<0):raise TimeOrderError("bad order")
        if self.time_value is not None:object.__setattr__(self,"time_value",finite(self.time_value,"time_value"))
        if self.simultaneous_group is not None:object.__setattr__(self,"simultaneous_group",tok(self.simultaneous_group,"simultaneous_group"))
@dataclass(frozen=True)
class Plan:
    plan_id:str;kind:str;status:str;ops:tuple[Mapping[str,Any],...];warnings:tuple[str,...];blockers:tuple[str,...];fingerprint:str;review_required:bool=True;accepted:bool=False
def plan(ctx,suffix,kind,status="PASS",ops=(),warnings=(),blockers=()):
    body={"id":ctx.intent_id+suffix,"kind":kind,"status":status,"ops":tuple(canon(dict(x)) for x in ops),"warnings":tuple(warnings),"blockers":tuple(blockers),"evidence":ctx.evidence_refs,"reasoning":ctx.reasoning_refs,"revision":ctx.source_revision,"accepted":False}
    return Plan(body["id"],kind,status,body["ops"],tuple(warnings),tuple(blockers),fp(body),True,False)
