from __future__ import annotations
from math import isfinite
from .scene_ir_contract import SceneElement, SceneIRError

class ElementSpecError(SceneIRError): pass

def tok(v,n):
    if not isinstance(v,str) or not v.strip(): raise ElementSpecError(f"{n} must be nonblank")
    return v.strip()

def num(v,n):
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not isfinite(float(v)):
        raise ElementSpecError(f"{n} must be finite numeric")
    return float(v)

def line(source_refs, reasoning_refs):
    if not source_refs or not reasoning_refs: raise ElementSpecError("source/reasoning lineage required")
    return tuple(source_refs), tuple(reasoning_refs)

def make(element_id, kind, source_refs, reasoning_refs, props, accessibility=None):
    source_refs, reasoning_refs = line(source_refs, reasoning_refs)
    return SceneElement(tok(element_id,"element_id"), kind, source_refs, reasoning_refs,
                        dict(props), dict(accessibility or {}))

def p2(v,n="point"):
    if not isinstance(v,(tuple,list)) or len(v)!=2: raise ElementSpecError(f"{n} must be 2D")
    return (num(v[0],n+".x"),num(v[1],n+".y"))

def p3(v,n="point"):
    if not isinstance(v,(tuple,list)) or len(v)!=3: raise ElementSpecError(f"{n} must be 3D")
    return (num(v[0],n+".x"),num(v[1],n+".y"),num(v[2],n+".z"))
