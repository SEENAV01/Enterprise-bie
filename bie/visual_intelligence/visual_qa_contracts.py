from __future__ import annotations
from dataclasses import dataclass, field
from hashlib import sha256
from math import isfinite
from typing import Any, Mapping
import json

class VisualQAValidationError(ValueError): pass
class SemanticAlignmentError(VisualQAValidationError): pass
class LayoutQAError(VisualQAValidationError): pass
class ClutterQAError(VisualQAValidationError): pass
class AssetQAError(VisualQAValidationError): pass
class VisualBenchmarkError(VisualQAValidationError): pass

def token(value, field_name):
    if not isinstance(value, str) or not value.strip():
        raise VisualQAValidationError(f"{field_name} must be nonblank")
    return value.strip()

def ids(values, field_name, allow_empty=False):
    out = tuple(token(v, field_name) for v in (values or ()))
    if not allow_empty and not out:
        raise VisualQAValidationError(f"{field_name} must not be empty")
    if len(set(out)) != len(out):
        raise VisualQAValidationError(f"{field_name} contains duplicates")
    return out

def score(value, field_name="score"):
    if isinstance(value, bool) or not isinstance(value, (int,float)):
        raise VisualQAValidationError(f"{field_name} must be numeric")
    value = float(value)
    if not isfinite(value) or not 0 <= value <= 1:
        raise VisualQAValidationError(f"{field_name} must be in [0,1]")
    return value

def number(value, field_name):
    if isinstance(value, bool) or not isinstance(value, (int,float)):
        raise VisualQAValidationError(f"{field_name} must be numeric")
    value = float(value)
    if not isfinite(value):
        raise VisualQAValidationError(f"{field_name} must be finite")
    return value

def canonical(value):
    if isinstance(value, Mapping):
        return {str(k): canonical(value[k]) for k in sorted(value, key=str)}
    if isinstance(value, (list,tuple)):
        return [canonical(v) for v in value]
    if isinstance(value, set):
        return sorted(canonical(v) for v in value)
    if isinstance(value, float):
        if not isfinite(value):
            raise VisualQAValidationError("non-finite payload")
        return value
    if value is None or isinstance(value, (str,int,bool)):
        return value
    raise VisualQAValidationError(f"unsupported payload type: {type(value).__name__}")

def fingerprint(payload):
    raw = json.dumps(canonical(payload), sort_keys=True, separators=(",",":"), ensure_ascii=False)
    return sha256(raw.encode("utf-8")).hexdigest()

@dataclass(frozen=True)
class Box:
    x: float
    y: float
    width: float
    height: float
    def __post_init__(self):
        x = number(self.x, "x"); y = number(self.y, "y")
        w = number(self.width, "width"); h = number(self.height, "height")
        if w <= 0 or h <= 0 or x < 0 or y < 0 or x+w > 1+1e-9 or y+h > 1+1e-9:
            raise LayoutQAError("box must stay inside normalized [0,1] canvas")
        object.__setattr__(self,"x",x); object.__setattr__(self,"y",y)
        object.__setattr__(self,"width",w); object.__setattr__(self,"height",h)
    @property
    def right(self): return self.x + self.width
    @property
    def bottom(self): return self.y + self.height
    @property
    def area(self): return self.width * self.height
    def intersection_area(self, other):
        return max(0,min(self.right,other.right)-max(self.x,other.x)) * max(0,min(self.bottom,other.bottom)-max(self.y,other.y))

@dataclass(frozen=True)
class VisualQAResult:
    qa_id: str
    dimension: str
    score: float
    passed: bool
    blockers: tuple[str,...]
    warnings: tuple[str,...]
    evidence_refs: tuple[str,...]
    reasoning_refs: tuple[str,...]
    metrics: Mapping[str,Any] = field(default_factory=dict)
    review_required: bool = True
    accepted: bool = False
    fingerprint: str = ""
    def __post_init__(self):
        object.__setattr__(self,"qa_id",token(self.qa_id,"qa_id"))
        object.__setattr__(self,"dimension",token(self.dimension,"dimension"))
        object.__setattr__(self,"score",score(self.score))
        object.__setattr__(self,"blockers",ids(self.blockers,"blockers",True))
        object.__setattr__(self,"warnings",ids(self.warnings,"warnings",True))
        object.__setattr__(self,"evidence_refs",ids(self.evidence_refs,"evidence_refs"))
        object.__setattr__(self,"reasoning_refs",ids(self.reasoning_refs,"reasoning_refs"))
        object.__setattr__(self,"metrics",canonical(dict(self.metrics)))
        if self.accepted:
            raise VisualQAValidationError("atomic QA cannot self-certify final acceptance")

def make_result(qa_id, dimension, score_value, blockers, warnings, evidence_refs, reasoning_refs, metrics):
    s = score(score_value)
    b = tuple(blockers); w = tuple(warnings)
    payload = {
        "qa_id":qa_id,"dimension":dimension,"score":s,"blockers":list(b),"warnings":list(w),
        "evidence_refs":list(evidence_refs),"reasoning_refs":list(reasoning_refs),"metrics":canonical(dict(metrics)),
        "review_required":True,"accepted":False
    }
    return VisualQAResult(
        qa_id,dimension,s,not b,b,w,tuple(evidence_refs),tuple(reasoning_refs),
        payload["metrics"],True,False,fingerprint(payload)
    )
