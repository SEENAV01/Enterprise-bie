def sync_quality(timeline):
    errors=[]; warnings=[]
    last=0
    for s in timeline.get("segments",[]):
        if s["timing"]["start_frame"]<last:
            errors.append("SEGMENT_OVERLAP")
        if s["timing"]["end_frame"]<s["timing"]["start_frame"]:
            errors.append("NEGATIVE_DURATION")
        last=s["timing"]["end_frame"]
    for c in timeline.get("cues",[]):
        if c["frame"]<0 or c["frame"]>timeline.get("duration_frames",0):
            errors.append("CUE_OUT_OF_RANGE")
    if timeline.get("duration_frames",0)==0:
        warnings.append("EMPTY_AUDIO_TIMELINE")
    return {"valid":not errors,"errors":errors,"warnings":warnings}
