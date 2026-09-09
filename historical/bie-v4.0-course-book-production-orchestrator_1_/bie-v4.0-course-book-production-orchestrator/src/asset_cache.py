def cache_key(asset):
    return "::".join([
      asset.get("semantic_id",""),
      asset.get("variant","default"),
      asset.get("style_version","1")
    ])

def build_asset_cache(assets):
    return {cache_key(a):a for a in assets}

def reusable_asset(cache, asset):
    return cache.get(cache_key(asset))
