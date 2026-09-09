def narration_segment(segment_id, script_block_id, text,
                     voice_id, start_sec=0, duration_sec=None,
                     pronunciation=None, emphasis=None):
    if not text or not script_block_id:
        raise ValueError("INVALID_NARRATION_SEGMENT")
    return {"segment_id":segment_id,"script_block_id":script_block_id,
            "text":text,"voice_id":voice_id,"start_sec":start_sec,
            "duration_sec":duration_sec,
            "pronunciation":pronunciation or {},
            "emphasis":emphasis or []}

def valid(n):
    return bool(n["segment_id"] and n["script_block_id"] and n["text"] and n["voice_id"])

def ordered(segments):
    return sorted(segments,key=lambda x:x["start_sec"])
