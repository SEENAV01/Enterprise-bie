from __future__ import annotations
from dataclasses import dataclass, field
from hashlib import sha256
from math import isfinite
from typing import Any, Mapping
import json

class MapAnimationError(ValueError): pass
class MapGroundingError(MapAnimationError): pass
class MapCRSError(MapAnimationError): pass
class MapTopologyError(MapAnimationError): pass

def tok(v,n):
    if not isinstance(v,str) or not v.strip():
        raise MapAnimationError(f"{n} must be nonblank")
    return v.strip()

def finite(v,n):
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not isfinite(float(v)):
        raise MapAnimationError(f"{n} must be finite numeric")
    return float(v)

def canonical(v):
    if isinstance(v,Mapping):
        return {str(k):canonical(v[k]) for k in sorted(v,key=str)}
    if isinstance(v,(list,tuple)):
        return [canonical(x) for x in v]
    if isinstance(v,set):
        return sorted(canonical(x) for x in v)
    if isinstance(v,float) and not isfinite(v):
        raise MapAnimationError("non-finite payload")
    if v is None or isinstance(v,(str,int,float,bool)):
        return v
    raise MapAnimationError(f"unsupported payload type: {type(v).__name__}")

def fp(payload):
    raw=json.dumps(canonical(payload),sort_keys=True,separators=(",",":"),ensure_ascii=False)
    return sha256(raw.encode("utf-8")).hexdigest()

@dataclass(frozen=True)
class MapContext:
    intent_id:str
    evidence_refs:tuple[str,...]
    reasoning_refs:tuple[str,...]
    visual_plan_fingerprint:str
    crs:str
    source_revision:int
    uncertainty:float=0.0
    payload:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        object.__setattr__(self,"intent_id",tok(self.intent_id,"intent_id"))
        if not self.evidence_refs or not self.reasoning_refs:
            raise MapGroundingError("evidence/reasoning lineage required")
        vf=tok(self.visual_plan_fingerprint,"visual_plan_fingerprint").lower()
        if len(vf)!=64 or any(c not in "0123456789abcdef" for c in vf):
            raise MapAnimationError("visual_plan_fingerprint must be SHA-256")
        object.__setattr__(self,"visual_plan_fingerprint",vf)
        object.__setattr__(self,"crs",tok(self.crs,"crs"))
        if isinstance(self.source_revision,bool) or not isinstance(self.source_revision,int) or self.source_revision<1:
            raise MapAnimationError("source_revision invalid")
        u=finite(self.uncertainty,"uncertainty")
        if not 0<=u<=1: raise MapAnimationError("uncertainty outside [0,1]")
        object.__setattr__(self,"uncertainty",u)
        object.__setattr__(self,"payload",canonical(dict(self.payload)))

@dataclass(frozen=True)
class MapView:
    view_id:str
    crs:str
    center:tuple[float,float]
    scale:float
    bearing_deg:float=0.0
    pitch_deg:float=0.0
    source_ref:str=""
    def __post_init__(self):
        object.__setattr__(self,"view_id",tok(self.view_id,"view_id"))
        object.__setattr__(self,"crs",tok(self.crs,"crs"))
        if len(self.center)!=2: raise MapAnimationError("center must be 2D")
        object.__setattr__(self,"center",(finite(self.center[0],"center.x"),finite(self.center[1],"center.y")))
        s=finite(self.scale,"scale")
        if s<=0: raise MapAnimationError("scale must be >0")
        object.__setattr__(self,"scale",s)
        object.__setattr__(self,"bearing_deg",finite(self.bearing_deg,"bearing_deg"))
        p=finite(self.pitch_deg,"pitch_deg")
        if not 0<=p<=90: raise MapAnimationError("pitch_deg outside [0,90]")
        object.__setattr__(self,"pitch_deg",p)
        object.__setattr__(self,"source_ref",tok(self.source_ref,"source_ref"))

@dataclass(frozen=True)
class MapAnimationPlan:
    plan_id:str
    kind:str
    status:str
    operations:tuple[Mapping[str,Any],...]
    warnings:tuple[str,...]
    blockers:tuple[str,...]
    crs:str
    evidence_refs:tuple[str,...]
    reasoning_refs:tuple[str,...]
    fingerprint:str
    review_required:bool=True
    accepted:bool=False

def make_plan(ctx, *, suffix, kind, status="PASS", operations=(), warnings=(), blockers=()):
    if status not in {"PASS","REVIEW","BLOCKED","UNSUPPORTED"}:
        raise MapAnimationError("invalid status")
    body={
        "plan_id":ctx.intent_id+suffix,"kind":tok(kind,"kind"),"status":status,
        "operations":tuple(canonical(dict(x)) for x in operations),
        "warnings":tuple(warnings),"blockers":tuple(blockers),"crs":ctx.crs,
        "evidence_refs":ctx.evidence_refs,"reasoning_refs":ctx.reasoning_refs,
        "source_revision":ctx.source_revision,"accepted":False
    }
    return MapAnimationPlan(body["plan_id"],body["kind"],status,body["operations"],tuple(warnings),tuple(blockers),
                            ctx.crs,ctx.evidence_refs,ctx.reasoning_refs,fp(body),True,False)
