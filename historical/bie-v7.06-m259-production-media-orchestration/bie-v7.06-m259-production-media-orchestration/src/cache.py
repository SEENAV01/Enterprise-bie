def cache_key(asset_id, fingerprint):
    return f"media:{asset_id}:{fingerprint}"

def cache_lookup(cache, key):
    return cache.get(key)

def cache_store(cache, key, artifact):
    cache[key]=artifact
    return artifact
