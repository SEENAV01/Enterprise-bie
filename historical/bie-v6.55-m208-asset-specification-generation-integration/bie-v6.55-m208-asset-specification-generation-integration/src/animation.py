def animation_spec(asset_id, duration_sec,
                    actions, easing=None, camera=None):
    if not actions:
        raise ValueError("ANIMATION_REQUIRES_ACTIONS")
    return {
        "asset_id": asset_id, "duration_sec": duration_sec,
        "actions": actions, "easing": easing,
        "camera": camera or {}
    }

def valid(item):
    return bool(item["asset_id"] and item["actions"])
