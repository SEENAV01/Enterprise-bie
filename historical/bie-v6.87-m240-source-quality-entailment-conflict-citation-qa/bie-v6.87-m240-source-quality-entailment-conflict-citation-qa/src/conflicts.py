def conflict_pair(a,b):
    if a.get("topic")!=b.get("topic"): return {"conflict":False}
    if a.get("polarity") is not None and b.get("polarity") is not None:
        return {"conflict":a["polarity"]!=b["polarity"],
                "claim_ids":[a.get("claim_id"),b.get("claim_id")]}
    return {"conflict":False}

def detect_conflicts(claims):
    out=[]
    for i,a in enumerate(claims):
        for b in claims[i+1:]:
            r=conflict_pair(a,b)
            if r.get("conflict"): out.append(r)
    return out
