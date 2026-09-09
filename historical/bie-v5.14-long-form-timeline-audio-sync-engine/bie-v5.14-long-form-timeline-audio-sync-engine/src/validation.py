def validate_timeline(tl):
    errors=[]
    if tl.get("fps",0)<=0: errors.append("INVALID_FPS")
    if tl.get("duration_frames",0)<0: errors.append("INVALID_DURATION")
    return {"valid":not errors,"errors":errors}
