def map_events(narrative_events, cues):
    # Match an event to the nearest cue after its requested semantic anchor.
    # Semantic anchors are produced by M41; this layer does not invent content.
    out=[]
    for e in narrative_events:
        anchor=e.get("anchor")
        candidates=[c for c in cues if anchor and c.get("text") and
                    anchor.lower() in c["text"].lower()]
        if candidates:
            c=candidates[0]
            out.append({"event_id":e["id"],"cue_id":c["id"],
                        "time_s":c["time_s"],"sync":"ANCHOR_MATCH"})
        elif "requested_time_s" in e:
            out.append({"event_id":e["id"],
                        "time_s":e["requested_time_s"],
                        "sync":"REQUESTED_TIME"})
        else:
            out.append({"event_id":e["id"],"time_s":None,
                        "sync":"UNRESOLVED"})
    return out
