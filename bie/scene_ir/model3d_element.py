from .element_common import *
def build(element_id,asset_ref,source_refs,reasoning_refs,coordinate_frame,scale=(1,1,1),rights_ref=None,accessibility=None):
    sc=tuple(num(x,"scale") for x in scale)
    if len(sc)!=3 or any(x<=0 for x in sc): raise ElementSpecError("invalid 3D scale")
    props={"asset_ref":tok(asset_ref,"asset_ref"),"coordinate_frame":tok(coordinate_frame,"coordinate_frame"),"scale":sc}
    if rights_ref is not None: props["rights_ref"]=tok(rights_ref,"rights_ref")
    return make(element_id,"model3d",source_refs,reasoning_refs,props,accessibility)
