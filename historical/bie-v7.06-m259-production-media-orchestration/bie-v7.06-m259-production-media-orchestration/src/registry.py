def register_asset(registry, asset_id, kind, uri, version, metadata=None):
    registry[asset_id]={"id":asset_id,"kind":kind,"uri":uri,"version":version,
                        "metadata":metadata or {}}
    return registry[asset_id]

def resolve_asset(registry, asset_id, version=None):
    item=registry.get(asset_id)
    if not item: return None
    if version is not None and item["version"]!=version: return None
    return item
