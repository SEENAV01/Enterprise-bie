def audio_cue(frame, action, payload=None):
    return {
      "frame":frame,
      "action":action,
      "payload":payload or {}
    }

def cue_set(cues):
    return sorted(cues,key=lambda x:x["frame"])
