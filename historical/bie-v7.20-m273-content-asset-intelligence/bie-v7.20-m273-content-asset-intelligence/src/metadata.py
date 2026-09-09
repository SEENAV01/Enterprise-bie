def build_metadata(asset_id, media_type, width=None, height=None, duration=None, **extra):
    return {"asset_id":asset_id,"media_type":media_type,"width":width,
            "height":height,"duration":duration,"metadata":extra}

def validate_metadata(meta):
    errors=[]
    if not meta.get("asset_id"): errors.append("ASSET_ID_REQUIRED")
    if not meta.get("media_type"): errors.append("MEDIA_TYPE_REQUIRED")
    if meta.get("width") is not None and meta["width"]<=0: errors.append("WIDTH_INVALID")
    if meta.get("height") is not None and meta["height"]<=0: errors.append("HEIGHT_INVALID")
    return {"valid":not errors,"errors":errors}
