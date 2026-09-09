def manifest(manifest_id, storyboard_id, assets,
             production_profile=None):
    return {
        "manifest_id": manifest_id,
        "storyboard_id": storyboard_id,
        "assets": assets,
        "production_profile": production_profile or {}
    }

def valid(item):
    return bool(item["manifest_id"] and item["storyboard_id"] and item["assets"])
