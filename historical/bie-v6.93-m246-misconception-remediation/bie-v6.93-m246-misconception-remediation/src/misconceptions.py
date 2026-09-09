def detect_misconception(responses):
    grouped={}
    for r in responses:
        if r.get("error",{}).get("type") not in (None,"NONE"):
            t=r["error"]["type"]; grouped[t]=grouped.get(t,0)+1
    return [{"type":k,"count":v,"confidence":min(1.0,v/2)} for k,v in grouped.items()]

def misconception_gate(items,min_confidence=0.5):
    return {"passed":all(x["confidence"]>=min_confidence for x in items),"items":items}
