def narration_segment(segment_id,text,start_frame,end_frame,
                     emphasis=None,phoneme_timing=None):
    return {"segment_id":segment_id,"text":text,
            "start_frame":start_frame,"end_frame":end_frame,
            "emphasis":emphasis or [],"phoneme_timing":phoneme_timing or []}

def pause(start_frame,end_frame,reason="NATURAL"):
    return {"type":"PAUSE","start_frame":start_frame,
            "end_frame":end_frame,"reason":reason}
