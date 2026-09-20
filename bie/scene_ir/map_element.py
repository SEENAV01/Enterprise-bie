from .element_common import *
def build(element_id,crs,layers,source_refs,reasoning_refs,extent=None,accessibility=None):
    layers=tuple(dict(x) for x in layers)
    if not layers: raise ElementSpecError("map layers required")
    for layer in layers:
        if not layer.get("layer_id") or not layer.get("kind"): raise ElementSpecError("layer identity/kind required")
    if extent is not None:
        if len(extent)!=4: raise ElementSpecError("extent must have four values")
        x0,y0,x1,y1=(num(x,"extent") for x in extent)
        if x1<=x0 or y1<=y0: raise ElementSpecError("invalid extent")
        extent=(x0,y0,x1,y1)
    return make(element_id,"map",source_refs,reasoning_refs,{"crs":tok(crs,"crs"),"layers":layers,"extent":extent},accessibility)
