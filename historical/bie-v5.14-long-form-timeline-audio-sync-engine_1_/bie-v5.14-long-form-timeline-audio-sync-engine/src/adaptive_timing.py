def adaptive_scene_duration(narration_end_frame,visual_end_frame,
                            tail_frames=0):
    return max(narration_end_frame,visual_end_frame)+tail_frames

def sync_check(narration_segments,visual_beats,captions):
    errors=[]
    ns={s["segment_id"]:s for s in narration_segments}
    for b in visual_beats:
        s=ns.get(b["segment_id"])
        if not s: errors.append("BEAT_WITHOUT_NARRATION")
        elif b["start_frame"]<s["start_frame"] or b["start_frame"]>s["end_frame"]:
            errors.append("BEAT_OUTSIDE_NARRATION")
    for c in captions:
        if c["end_frame"]<c["start_frame"]:
            errors.append("INVALID_CAPTION_RANGE")
    return {"valid":not errors,"errors":errors}
