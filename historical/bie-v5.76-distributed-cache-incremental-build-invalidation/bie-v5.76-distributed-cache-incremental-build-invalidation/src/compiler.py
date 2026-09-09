from fingerprint import fingerprint
from cache import cache_key

def compile_cache_key(node_type,input_value,
                      config=None,policy_version=None):
    inp=fingerprint(input_value)
    cfg=fingerprint(config) if config is not None else None
    return {"schema_version":"5.76",
            "input_fingerprint":inp,
            "cache_key":cache_key(node_type,inp,cfg,policy_version)}
