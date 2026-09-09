def validate_caption_sync(captions, audio_duration, tolerance=0.20):
    errors=[]; last=0
    for c in captions:
        if c["start"]<last or c["end"]<=c["start"]: errors.append("CAPTION_ORDER_OR_DURATION")
        if c["start"]<0 or c["end"]>audio_duration+tolerance: errors.append("CAPTION_OUTSIDE_AUDIO")
        if not c.get("text","").strip(): errors.append("CAPTION_TEXT_MISSING")
        last=c["end"]
    return {"valid":not errors,"errors":errors}
