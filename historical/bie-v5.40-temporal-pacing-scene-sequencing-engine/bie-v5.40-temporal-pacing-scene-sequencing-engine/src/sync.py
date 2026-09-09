def sync_event(event_id,event_type,target,source=None,
               offset=0.0):
    return {"event_id":event_id,"event_type":event_type,
            "target":target,"source":source,"offset":offset}

def sync_types():
    return ["NARRATION_CUE","VISUAL_CUE","AUDIO_CUE",
            "INTERACTION","FEEDBACK","STATE_CHANGE","USER_ACTION"]
