from identity import stable_hash
def cache_key(scene_ir, renderer_version, asset_manifest):
    return stable_hash({
      "scene_ir":scene_ir,
      "renderer_version":renderer_version,
      "asset_manifest":asset_manifest
    })

def cache_lookup(cache, key):
    return cache.get(key)

def cache_store(cache, key, artifact):
    cache[key]=artifact
    return artifact
