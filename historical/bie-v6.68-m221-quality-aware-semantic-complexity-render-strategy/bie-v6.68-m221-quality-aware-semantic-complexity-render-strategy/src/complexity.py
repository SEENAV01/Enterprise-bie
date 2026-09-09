def estimate_complexity(features):
    weights={"concepts":1.0,"equations":1.5,"diagrams":1.2,
             "simulation":2.5,"3d":3.0,"code":2.0,"assets":0.8}
    score=sum(max(0,features.get(k,0))*w for k,w in weights.items())
    if score>=12: level="EXTREME"
    elif score>=8: level="HIGH"
    elif score>=4: level="MEDIUM"
    else: level="LOW"
    return {"score":score,"level":level,"features":features}
