
from copy import deepcopy
class PolicyError(ValueError): pass
ALLOWED_KEYS={"model_policy","locale","deterministic","feature_flags","quality_gates","limits"}
def merge_policy(parent:dict, child:dict)->dict:
    unknown=(set(parent)|set(child))-ALLOWED_KEYS
    if unknown: raise PolicyError(f"unknown policy keys: {sorted(unknown)}")
    out=deepcopy(parent)
    for k,v in child.items():
        if isinstance(v,dict) and isinstance(out.get(k),dict):
            merged=deepcopy(out[k]); merged.update(v); out[k]=merged
        else: out[k]=deepcopy(v)
    return out
def policy_chain(*layers):
    out={}
    for layer in layers: out=merge_policy(out,layer)
    return out
