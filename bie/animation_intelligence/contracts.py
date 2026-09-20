from __future__ import annotations
from dataclasses import dataclass, field
from hashlib import sha256
from math import isfinite
from typing import Any, Mapping
import json

class AnimationSemanticError(ValueError): pass
class AnimationTimingError(AnimationSemanticError): pass

ACTIONS=("enter","exit","emphasize","reveal","transform","morph","trace","path_follow","camera","simulation_state")

def tok(v,n):
    if not isinstance(v,str) or not v.strip():
        raise AnimationSemanticError(f"{n} must be nonblank string")
    return v.strip()

def ids(values,n):
    out=tuple(tok(v,n) for v in values)
    if not out or len(set(out))!=len(out):
        raise AnimationSemanticError(f"{n} must be nonempty unique ids")
    return out

def unit(v,n):
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not isfinite(float(v)) or not 0<=float(v)<=1:
        raise AnimationSemanticError(f"{n} must be in [0,1]")
    return float(v)

def canonical(v):
    if isinstance(v,Mapping):
        return {str(k):canonical(v[k]) for k in sorted(v,key=str)}
    if isinstance(v,(list,tuple)):
        return [canonical(x) for x in v]
    if isinstance(v,set):
        return sorted(canonical(x) for x in v)
    if isinstance(v,float) and not isfinite(v):
        raise AnimationSemanticError("non-finite payload")
    if v is None or isinstance(v,(str,int,float,bool)):
        return v
    raise AnimationSemanticError(f"unsupported payload type: {type(v).__name__}")

def fp(v):
    raw=json.dumps(canonical(v),sort_keys=True,separators=(",",":"),ensure_ascii=False)
    return sha256(raw.encode("utf-8")).hexdigest()

@dataclass(frozen=True)
class CueWindow:
    cue_id:str
    start_ms:int
    end_ms:int
    narration_revision:int
    def __post_init__(self):
        object.__setattr__(self,"cue_id",tok(self.cue_id,"cue_id"))
        if isinstance(self.start_ms,bool) or not isinstance(self.start_ms,int) or self.start_ms<0:
            raise AnimationTimingError("start_ms invalid")
        if isinstance(self.end_ms,bool) or not isinstance(self.end_ms,int) or self.end_ms<=self.start_ms:
            raise AnimationTimingError("end_ms must exceed start_ms")
        if isinstance(self.narration_revision,bool) or not isinstance(self.narration_revision,int) or self.narration_revision<1:
            raise AnimationTimingError("narration_revision invalid")

@dataclass(frozen=True)
class VisualElementState:
    element_id:str
    semantic_role:str
    state_id:str
    source_refs:tuple[str,...]
    visible:bool=True
    active:bool=True
    identity_id:str|None=None
    geometry_kind:str="shape"
    payload:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        object.__setattr__(self,"element_id",tok(self.element_id,"element_id"))
        object.__setattr__(self,"semantic_role",tok(self.semantic_role,"semantic_role"))
        object.__setattr__(self,"state_id",tok(self.state_id,"state_id"))
        object.__setattr__(self,"source_refs",ids(self.source_refs,"source_refs"))
        if self.identity_id is not None:
            object.__setattr__(self,"identity_id",tok(self.identity_id,"identity_id"))
        object.__setattr__(self,"geometry_kind",tok(self.geometry_kind,"geometry_kind"))
        object.__setattr__(self,"payload",canonical(dict(self.payload)))

@dataclass(frozen=True)
class AnimationContext:
    intent_id:str
    semantic_goal:str
    evidence_refs:tuple[str,...]
    reasoning_refs:tuple[str,...]
    visual_plan_fingerprint:str
    cue:CueWindow
    visual_revision:int
    target_profile:str
    reduced_motion:bool=False
    uncertainty:float=0.0
    payload:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        object.__setattr__(self,"intent_id",tok(self.intent_id,"intent_id"))
        object.__setattr__(self,"semantic_goal",tok(self.semantic_goal,"semantic_goal"))
        object.__setattr__(self,"evidence_refs",ids(self.evidence_refs,"evidence_refs"))
        object.__setattr__(self,"reasoning_refs",ids(self.reasoning_refs,"reasoning_refs"))
        f=tok(self.visual_plan_fingerprint,"visual_plan_fingerprint").lower()
        if len(f)!=64 or any(c not in "0123456789abcdef" for c in f):
            raise AnimationSemanticError("visual_plan_fingerprint must be SHA-256")
        object.__setattr__(self,"visual_plan_fingerprint",f)
        if isinstance(self.visual_revision,bool) or not isinstance(self.visual_revision,int) or self.visual_revision<1:
            raise AnimationSemanticError("visual_revision invalid")
        object.__setattr__(self,"target_profile",tok(self.target_profile,"target_profile"))
        object.__setattr__(self,"uncertainty",unit(self.uncertainty,"uncertainty"))
        object.__setattr__(self,"payload",canonical(dict(self.payload)))

@dataclass(frozen=True)
class AnimationStep:
    step_id:str
    action:str
    target_ids:tuple[str,...]
    start_ms:int
    end_ms:int
    semantic_effect:str
    source_state_id:str|None=None
    target_state_id:str|None=None
    payload:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        object.__setattr__(self,"step_id",tok(self.step_id,"step_id"))
        if self.action not in ACTIONS:
            raise AnimationSemanticError("unsupported action")
        object.__setattr__(self,"target_ids",ids(self.target_ids,"target_ids"))
        if self.start_ms<0 or self.end_ms<=self.start_ms:
            raise AnimationTimingError("step timing invalid")
        object.__setattr__(self,"semantic_effect",tok(self.semantic_effect,"semantic_effect"))
        object.__setattr__(self,"payload",canonical(dict(self.payload)))

@dataclass(frozen=True)
class AnimationDecision:
    decision_id:str
    action:str|None
    status:str
    confidence:float
    steps:tuple[AnimationStep,...]
    rationale:tuple[str,...]
    evidence_refs:tuple[str,...]
    reasoning_refs:tuple[str,...]
    payload:Mapping[str,Any]
    fingerprint:str
    review_required:bool=True
    accepted:bool=False

def make_decision(ctx, suffix, action, status, confidence, steps=(), rationale=(), payload=None):
    if action is not None and action not in ACTIONS:
        raise AnimationSemanticError("invalid action")
    if status not in {"PASS","REVIEW","BLOCKED","UNSUPPORTED","ABSTAIN"}:
        raise AnimationSemanticError("invalid status")
    confidence=unit(confidence,"confidence")
    steps=tuple(steps)
    for s in steps:
        if s.start_ms<ctx.cue.start_ms or s.end_ms>ctx.cue.end_ms:
            raise AnimationTimingError("step escapes bound narration cue")
    body={
        "decision_id":ctx.intent_id+suffix,"action":action,"status":status,"confidence":confidence,
        "steps":[s.__dict__ for s in steps],"rationale":tuple(rationale),
        "evidence_refs":ctx.evidence_refs,"reasoning_refs":ctx.reasoning_refs,
        "visual_plan_fingerprint":ctx.visual_plan_fingerprint,"visual_revision":ctx.visual_revision,
        "payload":canonical(dict(payload or {})),"accepted":False
    }
    return AnimationDecision(ctx.intent_id+suffix,action,status,confidence,steps,tuple(rationale),
                             ctx.evidence_refs,ctx.reasoning_refs,body["payload"],fp(body),True,False)
