from .element_common import *
def build(element_id,target_element_ids,source_refs,reasoning_refs,mode="outline",accessibility=None):
    ids=tuple(tok(x,"target_element_id") for x in target_element_ids)
    if not ids or len(set(ids))!=len(ids): raise ElementSpecError("invalid highlight targets")
    if mode not in {"outline","fill","spotlight","underline"}: raise ElementSpecError("unsupported highlight mode")
    return make(element_id,"highlight",source_refs,reasoning_refs,{"target_element_ids":ids,"mode":mode},accessibility)
