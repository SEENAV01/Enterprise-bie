def rubric(rubric_id,dimensions,threshold=0.0,
           version="1"):
    return {"rubric_id":rubric_id,
            "dimensions":dimensions,
            "threshold":threshold,
            "version":version}

def weighted_score(scores,weights):
    if not scores: return 0.0
    total=sum(weights.get(k,0) for k in scores)
    if total<=0: return 0.0
    return sum(scores[k]*weights.get(k,0) for k in scores)/total
