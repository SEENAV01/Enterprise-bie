def validate(timeline):
    errors=[]; warnings=[]
    d=timeline.get("duration_s",0)
    if d<=0: errors.append("INVALID_DURATION")
    last=-1
    for e in timeline.get("events",[]):
        if e["time_s"]<last: errors.append("EVENT_ORDER")
        if e["time_s"]<0 or e["time_s"]>d: errors.append("EVENT_OUT_OF_RANGE")
        last=e["time_s"]
    for s in timeline.get("scenes",[]):
        if s["start_s"]<0 or s["end_s"]>d or s["end_s"]<=s["start_s"]:
            errors.append("INVALID_SCENE")
    unresolved=sum(1 for e in timeline.get("source_events",[])
                   if e.get("sync")=="UNRESOLVED")
    if unresolved:warnings.append("UNRESOLVED_EVENT_ANCHORS")
    return {"valid":not errors,"errors":errors,"warnings":warnings}
