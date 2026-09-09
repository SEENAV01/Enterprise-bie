def fuse_text_visual(text_claims, visual_claims):
    fused=[]
    for c in text_claims:
        fused.append({**c,"modalities":["text"]})
    for c in visual_claims:
        fused.append({**c,"modalities":["visual"]})
    return fused

def conflict_check(claims):
    # Conservative: exact duplicate wording is compatible; anything requiring
    # semantic comparison is routed to model review.
    out=[]
    for i,a in enumerate(claims):
        for b in claims[i+1:]:
            if a.get("text","").strip().lower()==b.get("text","").strip().lower():
                continue
            if a.get("topic")==b.get("topic"):
                out.append({"a":a.get("claim_id"),"b":b.get("claim_id"),"status":"MODEL_REVIEW"})
    return out
