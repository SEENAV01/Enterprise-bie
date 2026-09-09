def sync_narration(script_segments,timings):
    tm={x["segment_id"]:x for x in timings}
    return [{"segment_id":s["segment_id"],"text":s["text"],
             "start":tm[s["segment_id"]]["start"],
             "end":tm[s["segment_id"]]["end"]}
            for s in script_segments if s["segment_id"] in tm]

def validate_sync(sync):
    errors=[]
    last=-1
    for x in sync:
        if x["start"]<last: errors.append("NON_MONOTONIC_TIMELINE")
        if x["end"]<=x["start"]: errors.append("INVALID_DURATION")
        last=x["end"]
    return {"passed":not errors,"errors":errors}
