from .element_common import *
def build(element_id,components,source_refs,reasoning_refs,origin=None,unit=None,label=None,accessibility=None):
    c=tuple(num(x,"component") for x in components)
    if len(c) not in {2,3}: raise ElementSpecError("vector must be 2D or 3D")
    o=tuple(num(x,"origin") for x in (origin if origin is not None else (0,)*len(c)))
    if len(o)!=len(c): raise ElementSpecError("origin dimensionality mismatch")
    props={"components":c,"origin":o,"magnitude":sum(x*x for x in c)**0.5}
    if unit is not None: props["unit"]=tok(unit,"unit")
    if label is not None: props["label"]=tok(label,"label")
    return make(element_id,"vector",source_refs,reasoning_refs,props,accessibility)
