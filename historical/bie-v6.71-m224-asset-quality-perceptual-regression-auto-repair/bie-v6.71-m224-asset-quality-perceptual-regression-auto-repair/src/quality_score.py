def quality_score(asset,weights=None):
    w=weights or {"technical":0.25,"semantic":0.25,
                  "visual":0.30,"consistency":0.20}
    values={k:float(asset.get(k+"_score",0)) for k in w}
    score=sum(values[k]*w[k] for k in w)
    return {"score":score,"components":values}

def classify(score):
    if score>=0.9: return "EXCELLENT"
    if score>=0.75: return "GOOD"
    if score>=0.6: return "ACCEPTABLE"
    return "REJECT"
