from digest import manifest_digest

def cache_key(manifest):
    return manifest_digest(manifest)

def cache_hit(cache,manifest):
    return cache_key(manifest) in cache

def cache_store(cache,manifest,artifact_ref):
    out=dict(cache)
    out[cache_key(manifest)]=artifact_ref
    return out
