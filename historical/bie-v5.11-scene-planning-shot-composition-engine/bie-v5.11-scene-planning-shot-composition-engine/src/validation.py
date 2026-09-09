def validate_shot(shot):
    errors=[]
    if not shot.get("shot_id"): errors.append("MISSING_SHOT_ID")
    if not shot.get("narration_segment_ids"): errors.append("SHOT_WITHOUT_NARRATION")
    return {"valid":not errors,"errors":errors}

def validate_sequence(shots):
    errors=[]
    ids=[s.get("shot_id") for s in shots]
    if len(ids)!=len(set(ids)): errors.append("DUPLICATE_SHOT_ID")
    for i,s in enumerate(shots):
        if i and s.get("timing",{}).get("start_frame") is not None:
            prev=shots[i-1].get("timing",{}).get("end_frame")
            if prev is not None and s["timing"]["start_frame"]<prev:
                errors.append("SHOT_TIMING_OVERLAP")
    return {"valid":not errors,"errors":errors}
