from __future__ import annotations
from dataclasses import dataclass, field
from hashlib import sha256
from math import isfinite
from typing import Any, Mapping
import json

class AnimationQAError(ValueError): pass

def tok(v,n):
    if not isinstance(v,str) or not v.strip(): raise AnimationQAError(f"{n} must be nonblank")
    return v.strip()
def finite(v,n):
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not isfinite(float(v)): raise AnimationQAError(f"{n} finite numeric required")
    return float(v)
def unit(v,n):
    x=finite(v,n)
    if not 0<=x<=1: raise AnimationQAError(f"{n} outside [0,1]")
    return x
def canon(v):
    if isinstance(v,Mapping): return {str(k):canon(v[k]) for k in sorted(v,key=str)}
    if isinstance(v,(list,tuple)): return [canon(x) for x in v]
    if isinstance(v,set): return sorted(canon(x) for x in v)
    if v is None or isinstance(v,(str,int,float,bool)): return v
    raise AnimationQAError("unsupported payload")
def fp(v): return sha256(json.dumps(canon(v),sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

@dataclass(frozen=True)
class Event:
    event_id:str; action:str; targets:tuple[str,...]; start_ms:int; end_ms:int; purpose:str
    evidence_refs:tuple[str,...]; reasoning_refs:tuple[str,...]; narration_revision:int
    priority:float=.5; motion:float=.5; essential:bool=True; payload:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        object.__setattr__(self,"event_id",tok(self.event_id,"event_id"))
        object.__setattr__(self,"action",tok(self.action,"action"))
        object.__setattr__(self,"targets",tuple(tok(x,"target") for x in self.targets))
        if not self.targets or len(set(self.targets))!=len(self.targets): raise AnimationQAError("targets invalid")
        if self.start_ms<0 or self.end_ms<=self.start_ms: raise AnimationQAError("timing invalid")
        object.__setattr__(self,"purpose",tok(self.purpose,"purpose"))
        if not self.evidence_refs or not self.reasoning_refs: raise AnimationQAError("lineage required")
        if self.narration_revision<1: raise AnimationQAError("narration_revision invalid")
        object.__setattr__(self,"priority",unit(self.priority,"priority"))
        object.__setattr__(self,"motion",unit(self.motion,"motion"))
        object.__setattr__(self,"payload",canon(dict(self.payload)))

@dataclass(frozen=True)
class Result:
    qa_id:str; status:str; score:float|None; blockers:tuple[str,...]; warnings:tuple[str,...]
    payload:Mapping[str,Any]; fingerprint:str; review_required:bool=True; accepted:bool=False

def result(qa_id,status,score=None,blockers=(),warnings=(),payload=None):
    if status not in {"PASS","REVIEW","BLOCKED","NOT_RUN","UNSUPPORTED"}: raise AnimationQAError("bad status")
    if score is not None: score=unit(score,"score")
    body={"qa_id":qa_id,"status":status,"score":score,"blockers":tuple(blockers),"warnings":tuple(warnings),
          "payload":canon(dict(payload or {})),"accepted":False}
    return Result(tok(qa_id,"qa_id"),status,score,tuple(blockers),tuple(warnings),body["payload"],fp(body),True,False)
