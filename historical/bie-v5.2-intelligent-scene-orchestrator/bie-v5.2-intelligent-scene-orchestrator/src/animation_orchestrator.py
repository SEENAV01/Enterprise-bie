def coordinate(events):
    events=sorted(events,key=lambda e:e.get("frame",0))
    active=[]
    result=[]
    for e in events:
        start=e.get("frame",0)
        end=e.get("end_frame",start)
        active=[a for a in active if a["end_frame"]>start]
        result.append({
          **e,
          "simultaneous_count":len(active)+1,
          "coordination":"SEQUENCE" if len(active)>=3 else "PARALLEL_OK"
        })
        active.append({"end_frame":end})
    return result
