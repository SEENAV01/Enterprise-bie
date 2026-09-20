from __future__ import annotations
from dataclasses import dataclass, field
from hashlib import sha256
from math import isfinite
from typing import Any, Mapping, Sequence, Iterable
import json

class AssetValidationError(ValueError): pass
class AssetGroundingError(AssetValidationError): pass
class AssetRightsError(AssetValidationError): pass

def token(v, *, field_name):
    if not isinstance(v,str) or not v.strip(): raise AssetValidationError(f"{field_name} must be nonblank string")
    return v.strip()

def ids(values, *, field_name, allow_empty=False):
    out=tuple(token(v,field_name=field_name) for v in (values or ()))
    if not allow_empty and not out: raise AssetValidationError(f"{field_name} must not be empty")
    if len(set(out))!=len(out): raise AssetValidationError(f"{field_name} duplicates")
    return out

def conf(v, *, field_name="confidence"):
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not isfinite(float(v)) or not 0<=float(v)<=1:
        raise AssetValidationError(f"{field_name} must be in [0,1]")
    return float(v)

def canon(v):
    if isinstance(v,Mapping): return {str(k):canon(v[k]) for k in sorted(v,key=lambda x:str(x))}
    if isinstance(v,(list,tuple)): return [canon(x) for x in v]
    if isinstance(v,set): return sorted(canon(x) for x in v)
    if isinstance(v,float):
        if not isfinite(v): raise AssetValidationError("non-finite payload")
        return v
    if v is None or isinstance(v,(str,int,bool)): return v
    raise AssetValidationError(f"unsupported payload type {type(v).__name__}")

def fp(payload):
    return sha256(json.dumps(canon(payload),sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

@dataclass(frozen=True)
class AssetNeed:
    need_id:str
    semantic_role:str
    media_kinds:tuple[str,...]
    evidence_refs:tuple[str,...]
    reasoning_refs:tuple[str,...]
    required:bool=True
    priority:int=50
    constraints:Mapping[str,Any]=field(default_factory=dict)
    confidence:float=1.0
    def __post_init__(self):
        object.__setattr__(self,"need_id",token(self.need_id,field_name="need_id"))
        object.__setattr__(self,"semantic_role",token(self.semantic_role,field_name="semantic_role"))
        object.__setattr__(self,"media_kinds",ids(self.media_kinds,field_name="media_kinds"))
        object.__setattr__(self,"evidence_refs",ids(self.evidence_refs,field_name="evidence_refs"))
        object.__setattr__(self,"reasoning_refs",ids(self.reasoning_refs,field_name="reasoning_refs"))
        if isinstance(self.priority,bool) or not isinstance(self.priority,int) or not 0<=self.priority<=100: raise AssetValidationError("priority")
        object.__setattr__(self,"constraints",canon(dict(self.constraints)))
        object.__setattr__(self,"confidence",conf(self.confidence))

@dataclass(frozen=True)
class AssetCandidate:
    asset_id:str
    source_kind:str
    media_kind:str
    semantic_tags:tuple[str,...]
    provenance_refs:tuple[str,...]
    rights_id:str|None=None
    quality_score:float=0.0
    payload:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        object.__setattr__(self,"asset_id",token(self.asset_id,field_name="asset_id"))
        object.__setattr__(self,"source_kind",token(self.source_kind,field_name="source_kind"))
        object.__setattr__(self,"media_kind",token(self.media_kind,field_name="media_kind"))
        object.__setattr__(self,"semantic_tags",ids(self.semantic_tags,field_name="semantic_tags",allow_empty=True))
        object.__setattr__(self,"provenance_refs",ids(self.provenance_refs,field_name="provenance_refs"))
        object.__setattr__(self,"quality_score",conf(self.quality_score,field_name="quality_score"))
        object.__setattr__(self,"payload",canon(dict(self.payload)))

@dataclass(frozen=True)
class AssetDecision:
    need_id:str
    action:str
    selected_asset_id:str|None
    request:Mapping[str,Any]
    rationale:tuple[str,...]
    review_required:bool=True
    accepted:bool=False
    fingerprint:str=""
    def __post_init__(self):
        if self.accepted: raise AssetValidationError("atomic asset decision cannot self-accept")

def decision(need, action, *, selected=None, request=None, rationale=()):
    payload={"need_id":need.need_id,"action":action,"selected":selected,"request":canon(dict(request or {})),
             "rationale":list(rationale),"evidence_refs":list(need.evidence_refs),"reasoning_refs":list(need.reasoning_refs),
             "review_required":True,"accepted":False}
    return AssetDecision(need.need_id,action,selected,payload["request"],tuple(rationale),True,False,fp(payload))
