"""Original diagram builder, with an optional explicit compiler viewport.

The keyword-only addition preserves legacy calls and their exact props. Layout is
never inferred: callers choosing production diagram emission supply view_box.
"""
import math
from .element_common import *

def build(element_id,nodes,edges,source_refs,reasoning_refs,diagram_kind="concept",accessibility=None,*,view_box=None):
    nodes=tuple(dict(x) for x in nodes); edges=tuple(dict(x) for x in edges)
    if not nodes: raise ElementSpecError("nodes required")
    ids=[tok(n.get("node_id"),"node_id") for n in nodes]
    if len(set(ids))!=len(ids): raise ElementSpecError("duplicate node")
    valid=set(ids)
    for e in edges:
        if tok(e.get("from"),"from") not in valid or tok(e.get("to"),"to") not in valid: raise ElementSpecError("edge references unknown node")
    props={"diagram_kind":tok(diagram_kind,"diagram_kind"),"nodes":nodes,"edges":edges}
    if view_box is not None:
        if (not isinstance(view_box,(list,tuple)) or len(view_box)!=4
            or any(type(v) not in (int,float) or not math.isfinite(v) for v in view_box)
            or view_box[2]<=0 or view_box[3]<=0):
            raise ElementSpecError("view_box requires finite x,y and positive width,height")
        props["view_box"]=tuple(view_box)
    return make(element_id,"diagram",source_refs,reasoning_refs,props,accessibility)
