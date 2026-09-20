from .element_common import *
def build(element_id,vertices,source_refs,reasoning_refs,edges=(),accessibility=None):
    vs=tuple(p2(x,"vertex") for x in vertices)
    if len(vs)<2: raise ElementSpecError("2D model needs >=2 vertices")
    es=tuple(tuple(x) for x in edges)
    for e in es:
        if len(e)!=2 or any(not isinstance(i,int) or i<0 or i>=len(vs) for i in e): raise ElementSpecError("invalid edge")
    return make(element_id,"model2d",source_refs,reasoning_refs,{"vertices":vs,"edges":es},accessibility)
