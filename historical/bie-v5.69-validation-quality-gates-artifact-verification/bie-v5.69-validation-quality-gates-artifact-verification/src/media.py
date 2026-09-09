def media_constraints(duration=None,fps=None,width=None,height=None,
                     max_duration=None,required_fps=None):
    return {"duration":duration,"fps":fps,"width":width,"height":height,
            "max_duration":max_duration,"required_fps":required_fps}

def validate_media(meta,constraints):
    errors=[]
    if constraints.get("max_duration") is not None and meta.get("duration",0)>constraints["max_duration"]:
        errors.append("MAX_DURATION")
    if constraints.get("required_fps") is not None and meta.get("fps")!=constraints["required_fps"]:
        errors.append("FPS")
    return {"valid":not errors,"errors":errors}
