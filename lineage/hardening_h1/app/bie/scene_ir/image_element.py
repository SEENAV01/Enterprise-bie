from .element_common import *
def build(element_id,asset_ref,source_refs,reasoning_refs,rights_ref,alt_text,crop=None,accessibility=None):
    props={"asset_ref":tok(asset_ref,"asset_ref"),"rights_ref":tok(rights_ref,"rights_ref")}
    if crop is not None:
        if len(crop)!=4: raise ElementSpecError("crop must have four values")
        crop=tuple(num(x,"crop") for x in crop)
        if crop[2]<=0 or crop[3]<=0: raise ElementSpecError("invalid crop")
        props["crop"]=crop
    a=dict(accessibility or {}); a.setdefault("alt",tok(alt_text,"alt_text"))
    return make(element_id,"image",source_refs,reasoning_refs,props,a)
