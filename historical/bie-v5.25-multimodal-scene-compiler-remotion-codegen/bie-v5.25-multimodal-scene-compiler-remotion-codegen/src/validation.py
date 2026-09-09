def validate_scene_graph(scene):
    errors=[]
    if not scene.get("scene_id"): errors.append("MISSING_SCENE_ID")
    return {"valid":not errors,"errors":errors}

def validate_composition(comp):
    errors=[]
    for k in ("id","component","durationInFrames","fps","width","height"):
        if k not in comp: errors.append("MISSING_"+k.upper())
    if comp.get("durationInFrames",0)<=0: errors.append("INVALID_DURATION")
    return {"valid":not errors,"errors":errors}
