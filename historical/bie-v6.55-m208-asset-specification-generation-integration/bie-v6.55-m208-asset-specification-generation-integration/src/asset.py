SUPPORTED_ASSET_TYPES = {
    "IMAGE","DIAGRAM","CHART","EQUATION","ICON","CHARACTER",
    "BACKGROUND","ANIMATION","SCREEN_CAPTURE","AUDIO"
}

def asset(asset_id, asset_type, purpose, scene_id,
          description, requirements=None, evidence_ids=None):
    if asset_type not in SUPPORTED_ASSET_TYPES:
        raise ValueError("UNSUPPORTED_ASSET_TYPE")
    return {
        "asset_id": asset_id, "asset_type": asset_type,
        "purpose": purpose, "scene_id": scene_id,
        "description": description,
        "requirements": requirements or {},
        "evidence_ids": evidence_ids or []
    }

def valid(item):
    return bool(item["asset_id"] and item["purpose"] and
                item["scene_id"] and item["description"])
