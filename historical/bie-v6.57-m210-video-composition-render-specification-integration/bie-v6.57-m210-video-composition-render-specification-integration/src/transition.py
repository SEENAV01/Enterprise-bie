SUPPORTED_TRANSITIONS = {"CUT","FADE","DISSOLVE","WIPE","NONE"}

def transition(transition_id, transition_type, at_sec,
               duration_sec=0, from_scene=None, to_scene=None):
    if transition_type not in SUPPORTED_TRANSITIONS:
        raise ValueError("UNSUPPORTED_TRANSITION")
    return {"transition_id":transition_id,"transition_type":transition_type,
            "at_sec":at_sec,"duration_sec":duration_sec,
            "from_scene":from_scene,"to_scene":to_scene}

def valid(t):
    return bool(t["transition_id"]) and t["transition_type"] in SUPPORTED_TRANSITIONS
