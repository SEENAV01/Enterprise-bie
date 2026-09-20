from __future__ import annotations
from dataclasses import dataclass,field
from hashlib import sha256
from math import isfinite
from typing import Any,Mapping
import json

class ProjectionError(ValueError): pass
def tok(v,n):
    if not isinstance(v,str) or not v.strip(): raise ProjectionError(f"{n} blank")
    return v.strip()
def ids(v,n,empty=False):
    out=tuple(tok(x,n) for x in (v or ()))
    if not empty and not out: raise ProjectionError(f"{n} empty")
    if len(set(out))!=len(out): raise ProjectionError(f"{n} duplicates")
    return out
def canon(v):
    if isinstance(v,Mapping): return {str(k):canon(v[k]) for k in sorted(v,key=str)}
    if isinstance(v,(list,tuple)): return [canon(x) for x in v]
    if v is None or isinstance(v,(str,int,float,bool)): return v
    raise ProjectionError(type(v).__name__)
def fp(v): return sha256(json.dumps(canon(v),sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

@dataclass(frozen=True)
class GrammarElement:
    element_id:str; role:str; source_ids:tuple[str,...]; required:bool=True; group_id:str|None=None; parent_id:str|None=None; payload:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        object.__setattr__(self,"element_id",tok(self.element_id,"element_id"));object.__setattr__(self,"role",tok(self.role,"role"))
        object.__setattr__(self,"source_ids",ids(self.source_ids,"source_ids"))
        if self.group_id is not None: object.__setattr__(self,"group_id",tok(self.group_id,"group_id"))
        if self.parent_id is not None: object.__setattr__(self,"parent_id",tok(self.parent_id,"parent_id"))
        object.__setattr__(self,"payload",canon(dict(self.payload)))

@dataclass(frozen=True)
class GrammarRelation:
    relation_id:str; kind:str; source:str; target:str; source_ids:tuple[str,...]; payload:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        for n in ("relation_id","kind","source","target"): object.__setattr__(self,n,tok(getattr(self,n),n))
        object.__setattr__(self,"source_ids",ids(self.source_ids,"source_ids"));object.__setattr__(self,"payload",canon(dict(self.payload)))

@dataclass(frozen=True)
class LayoutNode:
    node_id:str; role:str; source_ids:tuple[str,...]; required:bool; group_id:str|None; parent_id:str|None; preferred_box:tuple[float,float,float,float]|None; payload:Mapping[str,Any]
@dataclass(frozen=True)
class LayoutConstraint:
    constraint_id:str; kind:str; node_ids:tuple[str,...]; value:float|None=None; hard:bool=True; source_relation_id:str|None=None
@dataclass(frozen=True)
class ProjectionTrace:
    element_id:str; disposition:str; layout_node_id:str|None; reason:str|None
@dataclass(frozen=True)
class LayoutProjection:
    nodes:tuple[LayoutNode,...]; constraints:tuple[LayoutConstraint,...]; relations:tuple[GrammarRelation,...]; trace:tuple[ProjectionTrace,...]; fingerprint:str; review_required:bool=True; accepted:bool=False

def project_grammar_to_layout(elements,relations,*,explicit_omissions=None):
    es=tuple(elements);rs=tuple(relations);om=dict(explicit_omissions or {})
    by={e.element_id:e for e in es}
    if len(by)!=len(es): raise ProjectionError("duplicate element ids")
    for r in rs:
        if r.source not in by or r.target not in by: raise ProjectionError("relation endpoint missing")
    nodes=[];trace=[]
    for e in es:
        if e.element_id in om:
            if e.required: raise ProjectionError(f"required element cannot be omitted: {e.element_id}")
            reason=tok(om[e.element_id],"omission reason");trace.append(ProjectionTrace(e.element_id,"OMITTED",None,reason));continue
        pb=e.payload.get("preferred_box")
        if pb is not None:
            if not isinstance(pb,(list,tuple)) or len(pb)!=4: raise ProjectionError("preferred_box must have 4 values")
            pb=tuple(float(x) for x in pb)
        nodes.append(LayoutNode(e.element_id,e.role,e.source_ids,e.required,e.group_id,e.parent_id,pb,e.payload))
        trace.append(ProjectionTrace(e.element_id,"PROJECTED",e.element_id,None))
    active={n.node_id for n in nodes};constraints=[]
    for e in es:
        if e.element_id in active and e.parent_id and e.parent_id in active:
            constraints.append(LayoutConstraint("parent:"+e.element_id,"contains",(e.parent_id,e.element_id),None,True,None))
    mapping={"contains":"contains","left_of":"left_of","above":"above","align_left":"align_left","align_top":"align_top",
             "non_overlap":"non_overlap","min_gap_x":"min_gap_x","min_gap_y":"min_gap_y"}
    for r in rs:
        if r.source not in active or r.target not in active: continue
        if r.kind in mapping:
            constraints.append(LayoutConstraint("rel:"+r.relation_id,mapping[r.kind],(r.source,r.target),r.payload.get("value"),True,r.relation_id))
    payload={"nodes":[n.__dict__ for n in nodes],"constraints":[c.__dict__ for c in constraints],
             "relations":[r.__dict__ for r in rs],"trace":[t.__dict__ for t in trace]}
    return LayoutProjection(tuple(nodes),tuple(constraints),rs,tuple(trace),fp(payload),True,False)
