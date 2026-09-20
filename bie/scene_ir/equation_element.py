from .element_common import *
def build(element_id,expression,source_refs,reasoning_refs,format="latex",side_conditions=(),accessibility=None):
    if format not in {"latex","mathml","plain"}: raise ElementSpecError("unsupported equation format")
    props={"expression":tok(expression,"expression"),"format":format,
           "side_conditions":tuple(tok(x,"side_condition") for x in side_conditions)}
    return make(element_id,"equation",source_refs,reasoning_refs,props,accessibility)
