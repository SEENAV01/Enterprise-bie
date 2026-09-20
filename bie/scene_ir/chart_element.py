from .element_common import *
def build(element_id,chart_kind,categories,values,source_refs,reasoning_refs,accessibility=None):
    if chart_kind not in {"bar","line","scatter","area","pie"}: raise ElementSpecError("unsupported chart")
    cats=tuple(tok(x,"category") for x in categories); vals=tuple(num(x,"value") for x in values)
    if not cats or len(cats)!=len(vals): raise ElementSpecError("category/value mismatch")
    if chart_kind=="pie" and any(v<0 for v in vals): raise ElementSpecError("negative pie value")
    return make(element_id,"chart",source_refs,reasoning_refs,{"chart_kind":chart_kind,"categories":cats,"values":vals},accessibility)
