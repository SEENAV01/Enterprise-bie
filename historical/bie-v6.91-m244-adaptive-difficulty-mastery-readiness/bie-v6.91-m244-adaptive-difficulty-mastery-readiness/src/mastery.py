def mastery_score(signal):
    weights={"assessment":0.5,"practice":0.2,"completion":0.1,"confidence":0.2}
    score=sum(float(signal.get(k,0))*w for k,w in weights.items())
    return round(max(0,min(1,score)),3)

def mastery_level(score):
    if score>=0.85:return "MASTERED"
    if score>=0.65:return "DEVELOPING"
    return "NOT_READY"
