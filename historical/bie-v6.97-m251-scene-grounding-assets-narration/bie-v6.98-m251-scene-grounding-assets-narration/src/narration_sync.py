def build_narration_segment(segment_id,text,start_frame,duration_frames,scene_id):
    return {"segment_id":segment_id,"scene_id":scene_id,"text":text,
            "start_frame":start_frame,"duration_frames":duration_frames,
            "end_frame":start_frame+duration_frames}

def validate_sync(segment, scene_start, scene_end):
    ok=segment["start_frame"]>=scene_start and segment["end_frame"]<=scene_end
    return {"valid":ok,"errors":[] if ok else ["NARRATION_OUT_OF_BOUNDS"]}
