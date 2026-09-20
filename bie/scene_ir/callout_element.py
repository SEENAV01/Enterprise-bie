from .element_common import *
def build(element_id,target_element_id,content,source_refs,reasoning_refs,placement="auto",accessibility=None):
    if placement not in {"auto","top","bottom","left","right"}: raise ElementSpecError("unsupported placement")
    return make(element_id,"callout",source_refs,reasoning_refs,{"target_element_id":tok(target_element_id,"target_element_id"),"content":tok(content,"content"),"placement":placement},accessibility)
