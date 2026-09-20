from .element_common import *
def build(element_id,model_ref,source_refs,reasoning_refs,initial_state,execution_class="conceptual",receipt_ref=None,accessibility=None):
    if execution_class not in {"conceptual","declared_model_output","verified_observed_execution"}: raise ElementSpecError("unsupported execution class")
    if execution_class=="verified_observed_execution" and not receipt_ref: raise ElementSpecError("verified execution requires receipt")
    props={"model_ref":tok(model_ref,"model_ref"),"initial_state":dict(initial_state),"execution_class":execution_class}
    if receipt_ref is not None: props["receipt_ref"]=tok(receipt_ref,"receipt_ref")
    return make(element_id,"simulation",source_refs,reasoning_refs,props,accessibility)
