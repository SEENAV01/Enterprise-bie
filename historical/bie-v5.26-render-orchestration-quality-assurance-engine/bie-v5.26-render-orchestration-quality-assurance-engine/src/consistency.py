def check_duration(audio_duration,scene_duration,tolerance=0.25):
    if audio_duration is None or scene_duration is None:
        return {"valid":False,"error":"MISSING_DURATION"}
    delta=abs(audio_duration-scene_duration)
    return {"valid":delta<=tolerance,"delta":delta}

def check_composition_frames(duration_seconds,fps,frames):
    expected=round(duration_seconds*fps)
    return {"valid":expected==frames,"expected":expected,"actual":frames}
