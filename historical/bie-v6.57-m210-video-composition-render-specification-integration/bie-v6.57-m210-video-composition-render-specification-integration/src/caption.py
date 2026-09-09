def caption(caption_id, text, start_sec, end_sec,
            style=None, source_ref=None):
    if end_sec < start_sec:
        raise ValueError("INVALID_CAPTION_RANGE")
    return {"caption_id":caption_id,"text":text,
            "start_sec":start_sec,"end_sec":end_sec,
            "style":style or {},"source_ref":source_ref}

def valid(c):
    return bool(c["caption_id"] and c["text"]) and c["end_sec"] >= c["start_sec"]
