def camera_plan(shots):
    planned=[]
    for i,s in enumerate(shots):
        planned.append({"shot_id":s["shot_id"],"start_frame":s["start_frame"],
                        "end_frame":s["end_frame"],"focus":s.get("focus"),
                        "scale":s.get("scale",1.0),"pan":s.get("pan",(0,0)),
                        "transition":s.get("transition","CUT")})
    return planned

def validate_camera(shots):
    errors=[]
    for s in shots:
        if s["end_frame"]<=s["start_frame"]: errors.append("INVALID_SHOT_RANGE")
        if s["scale"]<=0: errors.append("INVALID_CAMERA_SCALE")
    return {"valid":not errors,"errors":errors}
