SUPPORTED_VISUALS = {
    "TEXT","DIAGRAM","CHART","EQUATION","IMAGE","ICON",
    "CHARACTER","SCREEN_CAPTURE","ANIMATION","NONE"
}

def visual(visual_id, visual_type, description, scene_id,
           asset_ref=None, animation=None):
    if visual_type not in SUPPORTED_VISUALS:
        raise ValueError("UNSUPPORTED_VISUAL_TYPE")
    return {"visual_id":visual_id,"visual_type":visual_type,
            "description":description,"scene_id":scene_id,
            "asset_ref":asset_ref,"animation":animation}

def valid(item):
    return bool(item["visual_id"] and item["description"] and item["scene_id"])
