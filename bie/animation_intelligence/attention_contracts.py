from __future__ import annotations
from dataclasses import dataclass, field
from hashlib import sha256
from math import isfinite
from typing import Any, Mapping
import json

class AttentionError(ValueError): pass
class AttentionConflictError(AttentionError): pass
class AttentionTimingError(AttentionError): pass

def tok(v,n):
    if not isinstance(v,str) or not v.strip():
        raise AttentionError(f"{n} must be nonblank")
    return v.strip()

def ids(values,n,allow_empty=False):
    out=tuple(tok(v,n) for v in (values or ()))
    if not allow_empty and not out:
        raise AttentionError(f"{n} must not be empty")
    if len(set(out))!=len(out):
        raise AttentionError(f"{n} contains duplicates")
    return out

def unit(v,n):
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not isfinite(float(v)) or not 0<=float(v)<=1:
        raise AttentionError(f"{n} must be in [0,1]")
    return float(v)

def canonical(v):
    if isinstance(v,Mapping):
        return {str(k):canonical(v[k]) for k in sorted(v,key=str)}
    if isinstance(v,(list,tuple)):
        return [canonical(x) for x in v]
    if isinstance(v,set):
        return sorted(canonical(x) for x in v)
    if isinstance(v,float) and not isfinite(v):
        raise AttentionError("non-finite payload")
    if v is None or isinstance(v,(str,int,float,bool)):
        return v
    raise AttentionError(f"unsupported payload type {type(v).__name__}")

def fp(payload):
    raw=json.dumps(canonical(payload),sort_keys=True,separators=(",",":"),ensure_ascii=False)
    return sha256(raw.encode("utf-8")).hexdigest()

@dataclass(frozen=True)
class AttentionTarget:
    target_id:str
    semantic_role:str
    importance:float
    evidence_refs:tuple[str,...]
    reasoning_refs:tuple[str,...]
    motion_salience:float=0.0
    visual_salience:float=0.0
    active:bool=True
    payload:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        object.__setattr__(self,"target_id",tok(self.target_id,"target_id"))
        object.__setattr__(self,"semantic_role",tok(self.semantic_role,"semantic_role"))
        object.__setattr__(self,"importance",unit(self.importance,"importance"))
        object.__setattr__(self,"evidence_refs",ids(self.evidence_refs,"evidence_refs"))
        object.__setattr__(self,"reasoning_refs",ids(self.reasoning_refs,"reasoning_refs"))
        object.__setattr__(self,"motion_salience",unit(self.motion_salience,"motion_salience"))
        object.__setattr__(self,"visual_salience",unit(self.visual_salience,"visual_salience"))
        object.__setattr__(self,"payload",canonical(dict(self.payload)))

@dataclass(frozen=True)
class AttentionWindow:
    window_id:str
    target_ids:tuple[str,...]
    start_ms:int
    end_ms:int
    priority:float
    reason:str
    narration_revision:int
    exclusive:bool=True
    payload:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        object.__setattr__(self,"window_id",tok(self.window_id,"window_id"))
        object.__setattr__(self,"target_ids",ids(self.target_ids,"target_ids"))
        if isinstance(self.start_ms,bool) or not isinstance(self.start_ms,int) or self.start_ms<0:
            raise AttentionTimingError("start_ms invalid")
        if isinstance(self.end_ms,bool) or not isinstance(self.end_ms,int) or self.end_ms<=self.start_ms:
            raise AttentionTimingError("end_ms must exceed start_ms")
        object.__setattr__(self,"priority",unit(self.priority,"priority"))
        object.__setattr__(self,"reason",tok(self.reason,"reason"))
        if isinstance(self.narration_revision,bool) or not isinstance(self.narration_revision,int) or self.narration_revision<1:
            raise AttentionTimingError("narration_revision invalid")
        object.__setattr__(self,"payload",canonical(dict(self.payload)))

@dataclass(frozen=True)
class AttentionDecision:
    decision_id:str
    status:str
    primary_target:str|None
    secondary_targets:tuple[str,...]
    windows:tuple[AttentionWindow,...]
    blockers:tuple[str,...]
    warnings:tuple[str,...]
    evidence_refs:tuple[str,...]
    reasoning_refs:tuple[str,...]
    fingerprint:str
    review_required:bool=True
    accepted:bool=False

def make_decision(decision_id, *, status, primary_target, secondary_targets=(), windows=(),
                  blockers=(), warnings=(), evidence_refs=(), reasoning_refs=()):
    if status not in {"PASS","REVIEW","BLOCKED","UNSUPPORTED"}:
        raise AttentionError("invalid attention status")
    body={
        "decision_id":tok(decision_id,"decision_id"),
        "status":status,
        "primary_target":primary_target,
        "secondary_targets":tuple(secondary_targets),
        "windows":[w.__dict__ for w in windows],
        "blockers":tuple(blockers),
        "warnings":tuple(warnings),
        "evidence_refs":tuple(evidence_refs),
        "reasoning_refs":tuple(reasoning_refs),
        "accepted":False
    }
    return AttentionDecision(body["decision_id"],status,primary_target,tuple(secondary_targets),tuple(windows),
                             tuple(blockers),tuple(warnings),tuple(evidence_refs),tuple(reasoning_refs),
                             fp(body),True,False)
