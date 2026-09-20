from .element_common import *
def build(element_id,particle_count,source_refs,reasoning_refs,emitter,trajectory_mode="illustrative",physical_claim=False,receipt_ref=None,accessibility=None):
    if isinstance(particle_count,bool) or not isinstance(particle_count,int) or particle_count<1: raise ElementSpecError("invalid particle_count")
    if trajectory_mode not in {"illustrative","supplied","model_output"}: raise ElementSpecError("unsupported trajectory mode")
    if physical_claim and not receipt_ref: raise ElementSpecError("physical claim requires execution receipt")
    props={"particle_count":particle_count,"emitter":dict(emitter),"trajectory_mode":trajectory_mode,"physical_claim":bool(physical_claim)}
    if receipt_ref is not None: props["receipt_ref"]=tok(receipt_ref,"receipt_ref")
    return make(element_id,"particle_system",source_refs,reasoning_refs,props,accessibility)
