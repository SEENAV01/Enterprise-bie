from .element_common import *
def build(element_id,shape_kind,source_refs,reasoning_refs,geometry,style=None,accessibility=None):
    if shape_kind not in {"rectangle","circle","ellipse","line","polygon","polyline","arrow"}: raise ElementSpecError("unsupported shape")
    g=dict(geometry)
    if shape_kind in {"polygon","polyline"}:
        pts=tuple(p2(x) for x in g.get("points",()))
        if len(pts)<(3 if shape_kind=="polygon" else 2): raise ElementSpecError("insufficient points")
        g["points"]=pts
    return make(element_id,"shape",source_refs,reasoning_refs,{"shape_kind":shape_kind,"geometry":g,"style":dict(style or {})},accessibility)
