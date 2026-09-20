from .element_common import *
def build(element_id,asset_ref,source_refs,reasoning_refs,rights_ref,trim_start_ms=0,trim_end_ms=None,captions_ref=None,accessibility=None):
    if isinstance(trim_start_ms,bool) or not isinstance(trim_start_ms,int) or trim_start_ms<0: raise ElementSpecError("invalid trim start")
    if trim_end_ms is not None and (isinstance(trim_end_ms,bool) or not isinstance(trim_end_ms,int) or trim_end_ms<=trim_start_ms): raise ElementSpecError("invalid trim end")
    props={"asset_ref":tok(asset_ref,"asset_ref"),"rights_ref":tok(rights_ref,"rights_ref"),"trim_start_ms":trim_start_ms,"trim_end_ms":trim_end_ms}
    if captions_ref is not None: props["captions_ref"]=tok(captions_ref,"captions_ref")
    return make(element_id,"video",source_refs,reasoning_refs,props,accessibility)
