from .element_common import *
def build(element_id,series,source_refs,reasoning_refs,x_label,y_label,domain=None,accessibility=None):
    series=tuple(dict(s) for s in series)
    if not series: raise ElementSpecError("series required")
    for s in series:
        pts=tuple(p2(x,"graph_point") for x in s.get("points",()))
        if len(pts)<2: raise ElementSpecError("series needs >=2 points")
        s["points"]=pts
    if domain is not None:
        lo,hi=num(domain[0],"domain.low"),num(domain[1],"domain.high")
        if hi<=lo: raise ElementSpecError("invalid domain")
        domain=(lo,hi)
    return make(element_id,"graph",source_refs,reasoning_refs,{"series":series,"x_label":tok(x_label,"x_label"),"y_label":tok(y_label,"y_label"),"domain":domain},accessibility)
