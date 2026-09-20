from .element_common import *
def build(element_id,text,source_refs,reasoning_refs,role="body",language=None,accessibility=None):
    if role not in {"title","heading","body","caption","label","quote","code"}: raise ElementSpecError("unsupported text role")
    props={"text":tok(text,"text"),"role":role}
    if language is not None: props["language"]=tok(language,"language")
    return make(element_id,"text",source_refs,reasoning_refs,props,accessibility)
