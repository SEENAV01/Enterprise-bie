def cache_key(model_id, version, prompt):
    return f"{model_id}:{version}:{prompt}"

def get_cached(cache, key):
    return cache.get(key)

def put_cached(cache, key, result):
    cache[key]=result
    return result
