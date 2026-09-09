def check_structure(scene):
    errors=[]
    if not scene.get("scene_id"): errors.append("MISSING_SCENE_ID")
    if scene.get("duration_in_frames",0)<0: errors.append("INVALID_DURATION")
    return errors

def check_timing(scene):
    errors=[]
    for a in scene.get("animations",[]):
        frames=[k["frame"] for k in a.get("keyframes",[])]
        if frames!=sorted(frames): errors.append("UNSORTED_KEYFRAMES")
    return errors

def check_sync(scene):
    errors=[]
    for c in scene.get("captions",[]):
        if c.get("end_frame",0)<c.get("start_frame",0):
            errors.append("INVALID_CAPTION_TIMING")
    return errors
