from .element_common import *
def build(element_id,nodes,edges,source_refs,reasoning_refs,diagram_kind="concept",accessibility=None):
    nodes=tuple(dict(x) for x in nodes); edges=tuple(dict(x) for x in edges)
    if not nodes: raise ElementSpecError("nodes required")
    ids=[tok(n.get("node_id"),"node_id") for n in nodes]
    if len(set(ids))!=len(ids): raise ElementSpecError("duplicate node")
    valid=set(ids)
    for e in edges:
        if tok(e.get("from"),"from") not in valid or tok(e.get("to"),"to") not in valid: raise ElementSpecError("edge references unknown node")
    return make(element_id,"diagram",source_refs,reasoning_refs,{"diagram_kind":tok(diagram_kind,"diagram_kind"),"nodes":nodes,"edges":edges},accessibility)
