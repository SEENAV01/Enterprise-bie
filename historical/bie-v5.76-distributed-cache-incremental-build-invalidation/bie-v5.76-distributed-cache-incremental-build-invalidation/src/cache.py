def cache_key(node_type,input_fingerprint,
             config_fingerprint=None,policy_version=None):
    parts=[node_type,input_fingerprint,
           config_fingerprint or "",policy_version or ""]
    return ":".join(parts)

def cache_lookup(cache,key):
    return cache.get(key)

def cache_put(cache,key,artifact_ref):
    if key not in cache:
        cache[key]=artifact_ref
    return cache[key]
