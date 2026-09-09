def contradiction_pair(claim_a,claim_b,relation="UNKNOWN"):
    return {"claim_a":claim_a,"claim_b":claim_b,"relation":relation}

def detect_explicit_contradictions(pairs):
    return [p for p in pairs if p.get("relation")=="CONTRADICTS"]
