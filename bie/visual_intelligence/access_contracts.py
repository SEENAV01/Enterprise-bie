from __future__ import annotations
from dataclasses import dataclass, field
from hashlib import sha256
from math import isfinite
from typing import Any, Mapping, Sequence
import json

class AccessibilityValidationError(ValueError): pass
class ContrastError(AccessibilityValidationError): pass
class ReadabilityError(AccessibilityValidationError): pass
class EncodingError(AccessibilityValidationError): pass
class AltIntentError(AccessibilityValidationError): pass

def token(v, *, field_name):
    if not isinstance(v, str) or not v.strip():
        raise AccessibilityValidationError(f"{field_name} must be nonblank string")
    return v.strip()

def ids(values, *, field_name, allow_empty=False):
    out = tuple(token(v, field_name=field_name) for v in (values or ()))
    if not allow_empty and not out:
        raise AccessibilityValidationError(f"{field_name} must not be empty")
    if len(set(out)) != len(out):
        raise AccessibilityValidationError(f"{field_name} contains duplicates")
    return out

def finite(v, *, field_name):
    if isinstance(v, bool) or not isinstance(v, (int,float)) or not isfinite(float(v)):
        raise AccessibilityValidationError(f"{field_name} must be finite numeric")
    return float(v)

def canon(v):
    if isinstance(v, Mapping):
        return {str(k): canon(v[k]) for k in sorted(v, key=lambda x: str(x))}
    if isinstance(v, (list,tuple)):
        return [canon(x) for x in v]
    if isinstance(v, set):
        return sorted(canon(x) for x in v)
    if isinstance(v, float):
        if not isfinite(v):
            raise AccessibilityValidationError("non-finite payload")
        return v
    if v is None or isinstance(v, (str,int,bool)):
        return v
    raise AccessibilityValidationError(f"unsupported payload type: {type(v).__name__}")

def fp(payload):
    raw=json.dumps(canon(payload),sort_keys=True,separators=(",",":"),ensure_ascii=False)
    return sha256(raw.encode("utf-8")).hexdigest()

@dataclass(frozen=True)
class VisualAccessIntent:
    intent_id:str
    semantic_role:str
    evidence_refs:tuple[str,...]
    reasoning_refs:tuple[str,...]
    required:bool=True
    payload:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        object.__setattr__(self,"intent_id",token(self.intent_id,field_name="intent_id"))
        object.__setattr__(self,"semantic_role",token(self.semantic_role,field_name="semantic_role").lower())
        object.__setattr__(self,"evidence_refs",ids(self.evidence_refs,field_name="evidence_refs"))
        object.__setattr__(self,"reasoning_refs",ids(self.reasoning_refs,field_name="reasoning_refs"))
        object.__setattr__(self,"payload",canon(dict(self.payload)))

@dataclass(frozen=True)
class AccessibilityDecision:
    intent_id:str
    action:str
    payload:Mapping[str,Any]
    rationale:tuple[str,...]
    warnings:tuple[str,...]=()
    review_required:bool=True
    accepted:bool=False
    fingerprint:str=""
    def __post_init__(self):
        if self.accepted:
            raise AccessibilityValidationError("atomic accessibility decision cannot self-accept")

def decision(intent, *, action, payload=None, rationale=(), warnings=()):
    body={"intent_id":intent.intent_id,"action":action,"payload":canon(dict(payload or {})),
          "rationale":list(rationale),"warnings":list(warnings),
          "evidence_refs":list(intent.evidence_refs),"reasoning_refs":list(intent.reasoning_refs),
          "review_required":True,"accepted":False}
    return AccessibilityDecision(intent.intent_id,action,body["payload"],tuple(rationale),tuple(warnings),True,False,fp(body))
