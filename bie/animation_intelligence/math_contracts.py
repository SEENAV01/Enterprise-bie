from __future__ import annotations
from dataclasses import dataclass, field
from hashlib import sha256
from math import isfinite
from typing import Any, Mapping
import json

class MathAnimationError(ValueError): pass
class MathGroundingError(MathAnimationError): pass
class MathEquivalenceError(MathAnimationError): pass
class MathDomainError(MathAnimationError): pass

def tok(v,n):
    if not isinstance(v,str) or not v.strip():
        raise MathAnimationError(f"{n} must be nonblank")
    return v.strip()

def finite(v,n):
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not isfinite(float(v)):
        raise MathAnimationError(f"{n} must be finite numeric")
    return float(v)

def canonical(v):
    if isinstance(v,Mapping):
        return {str(k):canonical(v[k]) for k in sorted(v,key=str)}
    if isinstance(v,(list,tuple)):
        return [canonical(x) for x in v]
    if isinstance(v,set):
        return sorted(canonical(x) for x in v)
    if isinstance(v,float) and not isfinite(v):
        raise MathAnimationError("non-finite payload")
    if v is None or isinstance(v,(str,int,float,bool)):
        return v
    raise MathAnimationError(f"unsupported payload type: {type(v).__name__}")

def fp(payload):
    raw=json.dumps(canonical(payload),sort_keys=True,separators=(",",":"),ensure_ascii=False)
    return sha256(raw.encode("utf-8")).hexdigest()

@dataclass(frozen=True)
class MathContext:
    intent_id:str
    evidence_refs:tuple[str,...]
    reasoning_refs:tuple[str,...]
    visual_plan_fingerprint:str
    notation_system:str
    source_revision:int
    uncertainty:float=0.0
    payload:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        object.__setattr__(self,"intent_id",tok(self.intent_id,"intent_id"))
        if not self.evidence_refs or not self.reasoning_refs:
            raise MathGroundingError("evidence/reasoning lineage required")
        vf=tok(self.visual_plan_fingerprint,"visual_plan_fingerprint").lower()
        if len(vf)!=64 or any(c not in "0123456789abcdef" for c in vf):
            raise MathAnimationError("visual_plan_fingerprint must be SHA-256")
        object.__setattr__(self,"visual_plan_fingerprint",vf)
        object.__setattr__(self,"notation_system",tok(self.notation_system,"notation_system"))
        if isinstance(self.source_revision,bool) or not isinstance(self.source_revision,int) or self.source_revision<1:
            raise MathAnimationError("source_revision invalid")
        u=finite(self.uncertainty,"uncertainty")
        if not 0<=u<=1:
            raise MathAnimationError("uncertainty outside [0,1]")
        object.__setattr__(self,"uncertainty",u)
        object.__setattr__(self,"payload",canonical(dict(self.payload)))

@dataclass(frozen=True)
class MathPlan:
    plan_id:str
    kind:str
    status:str
    operations:tuple[Mapping[str,Any],...]
    warnings:tuple[str,...]
    blockers:tuple[str,...]
    fingerprint:str
    review_required:bool=True
    accepted:bool=False

def make_plan(ctx, *, suffix, kind, status="PASS", operations=(), warnings=(), blockers=()):
    if status not in {"PASS","REVIEW","BLOCKED","UNSUPPORTED"}:
        raise MathAnimationError("invalid status")
    body={
        "plan_id":ctx.intent_id+suffix,"kind":tok(kind,"kind"),"status":status,
        "operations":tuple(canonical(dict(x)) for x in operations),
        "warnings":tuple(warnings),"blockers":tuple(blockers),
        "evidence_refs":ctx.evidence_refs,"reasoning_refs":ctx.reasoning_refs,
        "notation_system":ctx.notation_system,"source_revision":ctx.source_revision,
        "accepted":False
    }
    return MathPlan(body["plan_id"],body["kind"],status,body["operations"],tuple(warnings),tuple(blockers),fp(body),True,False)
