def timeline(narration_segments, cues):
    events=[]
    for n in narration_segments:
        events.append(("NARRATION",n["start_sec"],
                       n.get("duration_sec") or 0,n["segment_id"]))
    for c in cues:
        events.append(("CUE",c["start_sec"],
                       c.get("duration_sec") or 0,c["cue_id"]))
    return sorted(events,key=lambda x:x[1])

def valid(tl):
    return all(x[1] >= 0 and x[2] >= 0 for x in tl)
