def validate_audio(audio, expected_duration, min_lufs=-24, max_lufs=-14):
    errors=[]
    if not audio.get("uri"): errors.append("AUDIO_MISSING")
    if audio.get("duration_seconds") is None: errors.append("AUDIO_DURATION_MISSING")
    elif abs(audio["duration_seconds"]-expected_duration)>0.25: errors.append("AUDIO_DURATION_MISMATCH")
    lufs=audio.get("lufs")
    if lufs is not None and not (min_lufs<=lufs<=max_lufs): errors.append("AUDIO_LOUDNESS_OUT_OF_RANGE")
    if audio.get("clipping",False): errors.append("AUDIO_CLIPPING")
    return {"valid":not errors,"errors":errors}
