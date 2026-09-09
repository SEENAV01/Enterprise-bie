def cache_entry(cache_key,artifact_ref,metadata=None):
    return {"cache_key":cache_key,"artifact_ref":artifact_ref,
            "metadata":metadata or {}}

def cache_lookup(cache,key):
    return cache.get(key)

def put_cache(cache,entry):
    cache[entry["cache_key"]]=entry
    return cache
