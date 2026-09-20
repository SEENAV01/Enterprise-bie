from __future__ import annotations
from dataclasses import dataclass, field
from hashlib import sha256
from math import isfinite
from typing import Any, Mapping
import json

class TextVisualValidationError(ValueError): pass
class TextGroundingError(TextVisualValidationError): pass
class PlacementError(TextVisualValidationError): pass
class DensityError(TextVisualValidationError): pass

def token(v, *, field_name):
    if not isinstance(v, str) or not v.strip():
        raise TextVisualValidationError(f"{field_name} must be nonblank string")
    return v.strip()

def ids(values, *, field_name, allow_empty=False):
    out=tuple(token(v, field_name=field_name) for v in (values or ()))
    if not allow_empty and not out:
        raise TextVisualValidationError(f"{field_name} must not be empty")
    if len(set(out)) != len(out):
        raise TextVisualValidationError(f"{field_name} contains duplicates")
    return out

def finite(v, *, field_name):
    if isinstance(v, bool) or not isinstance(v, (int,float)) or not isfinite(float(v)):
        raise TextVisualValidationError(f"{field_name} must be finite numeric")
    return float(v)

def canon(v):
    if isinstance(v, Mapping):
        return {str(k):canon(v[k]) for k in sorted(v, key=lambda x:str(x))}
    if isinstance(v, (list,tuple)):
        return [canon(x) for x in v]
    if isinstance(v, set):
        return sorted(canon(x) for x in v)
    if isinstance(v, float):
        if not isfinite(v): raise TextVisualValidationError("non-finite payload")
        return v
    if v is None or isinstance(v,(str,int,bool)):
        return v
    raise TextVisualValidationError(f"unsupported payload type: {type(v).__name__}")

def fp(payload):
    raw=json.dumps(canon(payload),sort_keys=True,separators=(",",":"),ensure_ascii=False)
    return sha256(raw.encode("utf-8")).hexdigest()

@dataclass(frozen=True)
class TextIntent:
    text_id:str
    text:str
    role:str
    evidence_refs:tuple[str,...]
    reasoning_refs:tuple[str,...]
    required:bool=True
    priority:int=50
    max_chars:int=140
    language:str="und"
    payload:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        object.__setattr__(self,"text_id",token(self.text_id,field_name="text_id"))
        object.__setattr__(self,"text",token(self.text,field_name="text"))
        object.__setattr__(self,"role",token(self.role,field_name="role").lower())
        object.__setattr__(self,"evidence_refs",ids(self.evidence_refs,field_name="evidence_refs"))
        object.__setattr__(self,"reasoning_refs",ids(self.reasoning_refs,field_name="reasoning_refs"))
        if isinstance(self.priority,bool) or not isinstance(self.priority,int) or not 0<=self.priority<=100:
            raise TextVisualValidationError("priority must be integer in [0,100]")
        if isinstance(self.max_chars,bool) or not isinstance(self.max_chars,int) or self.max_chars<1:
            raise TextVisualValidationError("max_chars must be positive integer")
        object.__setattr__(self,"language",token(self.language,field_name="language"))
        object.__setattr__(self,"payload",canon(dict(self.payload)))

@dataclass(frozen=True)
class Box:
    x:float; y:float; width:float; height:float
    def __post_init__(self):
        vals=[finite(self.x,field_name="x"),finite(self.y,field_name="y"),finite(self.width,field_name="width"),finite(self.height,field_name="height")]
        x,y,w,h=vals
        if w<=0 or h<=0 or x<0 or y<0 or x+w>1+1e-9 or y+h>1+1e-9:
            raise PlacementError("box must stay inside normalized canvas with positive dimensions")
        object.__setattr__(self,"x",x);object.__setattr__(self,"y",y);object.__setattr__(self,"width",w);object.__setattr__(self,"height",h)
    @property
    def right(self): return self.x+self.width
    @property
    def bottom(self): return self.y+self.height
    def intersects(self,other):
        return max(0,min(self.right,other.right)-max(self.x,other.x))*max(0,min(self.bottom,other.bottom)-max(self.y,other.y))>1e-9

@dataclass(frozen=True)
class TextDecision:
    text_id:str
    action:str
    display_text:str
    box:Box|None
    style:Mapping[str,Any]
    rationale:tuple[str,...]
    warnings:tuple[str,...]=()
    review_required:bool=True
    accepted:bool=False
    fingerprint:str=""
    def __post_init__(self):
        if self.accepted:
            raise TextVisualValidationError("atomic text decision cannot self-accept")

def decision(intent, *, action, display_text=None, box=None, style=None, rationale=(), warnings=()):
    shown=intent.text if display_text is None else str(display_text)
    payload={"text_id":intent.text_id,"action":action,"display_text":shown,
             "box":None if box is None else {"x":box.x,"y":box.y,"width":box.width,"height":box.height},
             "style":canon(dict(style or {})),"rationale":list(rationale),"warnings":list(warnings),
             "evidence_refs":list(intent.evidence_refs),"reasoning_refs":list(intent.reasoning_refs),
             "review_required":True,"accepted":False}
    return TextDecision(intent.text_id,action,shown,box,payload["style"],tuple(rationale),tuple(warnings),True,False,fp(payload))
