from .element_common import *
def build(element_id,target_element_id,text,source_refs,reasoning_refs,anchor=None,accessibility=None):
    props={"target_element_id":tok(target_element_id,"target_element_id"),"text":tok(text,"text")}
    if anchor is not None: props["anchor"]=p2(anchor,"anchor")
    return make(element_id,"annotation",source_refs,reasoning_refs,props,accessibility)
