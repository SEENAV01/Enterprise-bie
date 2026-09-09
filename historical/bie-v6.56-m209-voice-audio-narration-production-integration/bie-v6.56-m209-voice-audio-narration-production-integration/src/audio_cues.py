SUPPORTED_CUES = {"MUSIC","SFX","PAUSE","EMPHASIS","DUCK","FADE_IN","FADE_OUT"}

def cue(cue_id, cue_type, start_sec, duration_sec=0,
        asset_ref=None, level_db=None):
    if cue_type not in SUPPORTED_CUES:
        raise ValueError("UNSUPPORTED_AUDIO_CUE")
    return {"cue_id":cue_id,"cue_type":cue_type,"start_sec":start_sec,
            "duration_sec":duration_sec,"asset_ref":asset_ref,
            "level_db":level_db}

def valid(c):
    return bool(c["cue_id"]) and c["cue_type"] in SUPPORTED_CUES
