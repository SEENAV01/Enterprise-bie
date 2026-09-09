def validate_render(manifest,rendered):
    errors=[]
    for key in ["width","height","fps"]:
        if manifest.get(key)!=rendered.get(key):
            errors.append(f"{key.upper()}_MISMATCH")
    if rendered.get("duration_frames",0)<=0:
        errors.append("EMPTY_RENDER")
    return {"valid":not errors,"errors":errors}
