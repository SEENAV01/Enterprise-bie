def narration_segment(segment_id,text,scene_id=None,
                     start_hint=None,end_hint=None,emphasis=None):
    return {"segment_id":segment_id,"scene_id":scene_id,"text":text,
            "start_hint":start_hint,"end_hint":end_hint,
            "emphasis":emphasis or []}
