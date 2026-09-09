def audio_track(audio_path,duration_s,volume=1.0):
    return {
      "src":audio_path,
      "duration_s":duration_s,
      "volume":volume,
      "sync":"ABSOLUTE_TIMELINE_START"
    }

def cue_binding(event_id,frame,action):
    return {"event_id":event_id,"frame":frame,"action":action}
