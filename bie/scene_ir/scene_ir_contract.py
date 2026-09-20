from __future__ import annotations
from dataclasses import dataclass, field
from hashlib import sha256
from math import isfinite
from typing import Any, Mapping
import json

SCENE_IR_SCHEMA_VERSION="1.0.0"
class SceneIRError(ValueError):pass

def tok(v,n):
    if not isinstance(v,str) or not v.strip():raise SceneIRError(f"{n} blank")
    return v.strip()
def canon(v):
    if isinstance(v,Mapping):return {str(k):canon(v[k]) for k in sorted(v,key=str)}
    if isinstance(v,(tuple,list)):return [canon(x) for x in v]
    if isinstance(v,set):return sorted(canon(x) for x in v)
    if isinstance(v,float) and not isfinite(v):raise SceneIRError("non-finite payload")
    if v is None or isinstance(v,(str,int,float,bool)):return v
    raise SceneIRError("unsupported payload")
def fp(v):
    return sha256(json.dumps(canon(v),sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

@dataclass(frozen=True)
class SceneElement:
    element_id:str
    element_type:str
    source_refs:tuple[str,...]
    reasoning_refs:tuple[str,...]
    props:Mapping[str,Any]=field(default_factory=dict)
    accessibility:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        object.__setattr__(self,"element_id",tok(self.element_id,"element_id"))
        object.__setattr__(self,"element_type",tok(self.element_type,"element_type"))
        if not self.source_refs or not self.reasoning_refs:raise SceneIRError("element lineage required")
        object.__setattr__(self,"source_refs",tuple(tok(x,"source_ref") for x in self.source_refs))
        object.__setattr__(self,"reasoning_refs",tuple(tok(x,"reasoning_ref") for x in self.reasoning_refs))
        object.__setattr__(self,"props",canon(dict(self.props)))
        object.__setattr__(self,"accessibility",canon(dict(self.accessibility)))

@dataclass(frozen=True)
class SceneTrack:
    track_id:str
    element_id:str
    action:str
    start_ms:int
    end_ms:int
    parameters:Mapping[str,Any]=field(default_factory=dict)
    source_refs:tuple[str,...]=()
    reasoning_refs:tuple[str,...]=()
    def __post_init__(self):
        object.__setattr__(self,"track_id",tok(self.track_id,"track_id"))
        object.__setattr__(self,"element_id",tok(self.element_id,"element_id"))
        object.__setattr__(self,"action",tok(self.action,"action"))
        if isinstance(self.start_ms,bool) or not isinstance(self.start_ms,int) or self.start_ms<0:raise SceneIRError("bad start_ms")
        if isinstance(self.end_ms,bool) or not isinstance(self.end_ms,int) or self.end_ms<=self.start_ms:raise SceneIRError("bad end_ms")
        object.__setattr__(self,"parameters",canon(dict(self.parameters)))

@dataclass(frozen=True)
class SceneIR:
    scene_id:str
    schema_version:str
    title:str
    duration_ms:int
    elements:tuple[SceneElement,...]
    tracks:tuple[SceneTrack,...]
    source_refs:tuple[str,...]
    reasoning_refs:tuple[str,...]
    compiler_capabilities:tuple[str,...]=()
    metadata:Mapping[str,Any]=field(default_factory=dict)
    ir_fingerprint:str=""
    review_required:bool=True
    accepted:bool=False
    def __post_init__(self):
        object.__setattr__(self,"scene_id",tok(self.scene_id,"scene_id"))
        object.__setattr__(self,"title",tok(self.title,"title"))
        if self.schema_version!=SCENE_IR_SCHEMA_VERSION:raise SceneIRError("unsupported schema_version")
        if isinstance(self.duration_ms,bool) or not isinstance(self.duration_ms,int) or self.duration_ms<1:raise SceneIRError("bad duration")
        elements=tuple(self.elements);tracks=tuple(self.tracks)
        if not elements:raise SceneIRError("elements required")
        if len({e.element_id for e in elements})!=len(elements):raise SceneIRError("duplicate element id")
        if len({t.track_id for t in tracks})!=len(tracks):raise SceneIRError("duplicate track id")
        valid={e.element_id for e in elements}
        for t in tracks:
            if t.element_id not in valid:raise SceneIRError("unknown track element")
            if t.end_ms>self.duration_ms:raise SceneIRError("track exceeds duration")
        if not self.source_refs or not self.reasoning_refs:raise SceneIRError("scene lineage required")
        object.__setattr__(self,"elements",elements);object.__setattr__(self,"tracks",tracks)
        object.__setattr__(self,"metadata",canon(dict(self.metadata)))
        calc=fp(self.to_dict(False))
        if self.ir_fingerprint and self.ir_fingerprint!=calc:raise SceneIRError("fingerprint mismatch")
        object.__setattr__(self,"ir_fingerprint",calc)
    def to_dict(self,include_fp=True):
        d={"scene_id":self.scene_id,"schema_version":self.schema_version,"title":self.title,
           "duration_ms":self.duration_ms,"elements":[e.__dict__ for e in self.elements],
           "tracks":[t.__dict__ for t in self.tracks],"source_refs":self.source_refs,
           "reasoning_refs":self.reasoning_refs,"compiler_capabilities":self.compiler_capabilities,
           "metadata":self.metadata,"review_required":True,"accepted":False}
        if include_fp:d["ir_fingerprint"]=self.ir_fingerprint
        return canon(d)
