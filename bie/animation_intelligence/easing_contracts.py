from __future__ import annotations
from dataclasses import dataclass, field
from hashlib import sha256
from math import isfinite
from typing import Any, Mapping
import json

class EasingError(ValueError): pass
class DurationError(EasingError): pass
class SpringRuleError(EasingError): pass
class MotionReductionError(EasingError): pass

def tok(v,n):
    if not isinstance(v,str) or not v.strip():
        raise EasingError(f"{n} must be nonblank")
    return v.strip()

def finite(v,n):
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not isfinite(float(v)):
        raise EasingError(f"{n} must be finite numeric")
    return float(v)

def unit(v,n):
    x=finite(v,n)
    if not 0<=x<=1:
        raise EasingError(f"{n} must be in [0,1]")
    return x

def canonical(v):
    if isinstance(v,Mapping):
        return {str(k):canonical(v[k]) for k in sorted(v,key=str)}
    if isinstance(v,(list,tuple)):
        return [canonical(x) for x in v]
    if isinstance(v,set):
        return sorted(canonical(x) for x in v)
    if isinstance(v,float) and not isfinite(v):
        raise EasingError("non-finite payload")
    if v is None or isinstance(v,(str,int,float,bool)):
        return v
    raise EasingError(f"unsupported payload type: {type(v).__name__}")

def fp(payload):
    raw=json.dumps(canonical(payload),sort_keys=True,separators=(",",":"),ensure_ascii=False)
    return sha256(raw.encode("utf-8")).hexdigest()

@dataclass(frozen=True)
class MotionContext:
    intent_id:str
    semantic_action:str
    evidence_refs:tuple[str,...]
    reasoning_refs:tuple[str,...]
    visual_plan_fingerprint:str
    narration_revision:int
    reduced_motion_requested:bool=False
    semantic_importance:float=0.5
    complexity:float=0.5
    payload:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        object.__setattr__(self,"intent_id",tok(self.intent_id,"intent_id"))
        object.__setattr__(self,"semantic_action",tok(self.semantic_action,"semantic_action"))
        if not self.evidence_refs or not self.reasoning_refs:
            raise EasingError("evidence/reasoning lineage required")
        vf=tok(self.visual_plan_fingerprint,"visual_plan_fingerprint").lower()
        if len(vf)!=64 or any(c not in "0123456789abcdef" for c in vf):
            raise EasingError("visual_plan_fingerprint must be SHA-256")
        object.__setattr__(self,"visual_plan_fingerprint",vf)
        if isinstance(self.narration_revision,bool) or not isinstance(self.narration_revision,int) or self.narration_revision<1:
            raise EasingError("narration_revision invalid")
        object.__setattr__(self,"semantic_importance",unit(self.semantic_importance,"semantic_importance"))
        object.__setattr__(self,"complexity",unit(self.complexity,"complexity"))
        object.__setattr__(self,"payload",canonical(dict(self.payload)))

@dataclass(frozen=True)
class MotionPolicy:
    policy_id:str
    status:str
    easing:str
    duration_ms:int|None
    parameters:Mapping[str,Any]
    warnings:tuple[str,...]
    blockers:tuple[str,...]
    fingerprint:str
    review_required:bool=True
    accepted:bool=False

def make_policy(ctx, *, suffix, status="PASS", easing="linear", duration_ms=None,
                parameters=None, warnings=(), blockers=()):
    if status not in {"PASS","REVIEW","BLOCKED","UNSUPPORTED"}:
        raise EasingError("invalid policy status")
    if duration_ms is not None and (isinstance(duration_ms,bool) or not isinstance(duration_ms,int) or duration_ms<1):
        raise DurationError("duration_ms must be positive integer")
    body={
        "policy_id":ctx.intent_id+suffix,"status":status,"easing":tok(easing,"easing"),
        "duration_ms":duration_ms,"parameters":canonical(dict(parameters or {})),
        "warnings":tuple(warnings),"blockers":tuple(blockers),
        "semantic_action":ctx.semantic_action,"narration_revision":ctx.narration_revision,
        "evidence_refs":ctx.evidence_refs,"reasoning_refs":ctx.reasoning_refs,"accepted":False
    }
    return MotionPolicy(body["policy_id"],status,body["easing"],duration_ms,body["parameters"],
                        tuple(warnings),tuple(blockers),fp(body),True,False)
