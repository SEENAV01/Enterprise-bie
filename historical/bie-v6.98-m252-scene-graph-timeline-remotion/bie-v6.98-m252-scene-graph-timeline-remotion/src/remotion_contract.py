def build_remotion_scene(scene_id, duration_frames, fps, layers, camera, timeline, audio=None):
    return {"scene_id":scene_id,"duration_in_frames":duration_frames,"fps":fps,
            "layers":layers,"camera":camera,"timeline":timeline,"audio":audio or [],
            "renderer":"remotion"}

def validate_remotion_scene(scene):
    errors=[]
    if scene["duration_in_frames"]<=0: errors.append("INVALID_DURATION")
    if scene["fps"]<=0: errors.append("INVALID_FPS")
    for e in scene["timeline"]:
        if e.get("end_frame",0)>scene["duration_in_frames"]: errors.append("TIMELINE_OUT_OF_BOUNDS")
    for s in scene["camera"]:
        if s["end_frame"]>scene["duration_in_frames"]: errors.append("CAMERA_OUT_OF_BOUNDS")
    return {"valid":not errors,"errors":errors}
