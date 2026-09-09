def resolve_duration(audio):
    if audio.get("duration_s") is not None:
        return float(audio["duration_s"])
    words=audio.get("words",[])
    if words:
        return max(float(w.get("end_s",0)) for w in words)
    raise ValueError("AUDIO_DURATION_REQUIRED")
