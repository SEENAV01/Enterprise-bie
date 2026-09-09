def rank_source(source,weights=None):
    weights=weights or {"authority":0.4,"recency":0.2,"specificity":0.2,"stability":0.2}
    scores={k:float(source.get(k,0)) for k in weights}
    total=sum(scores[k]*weights[k] for k in weights)
    return {"source_id":source.get("source_id"),"score":round(total,3),"dimensions":scores}

def validate_quality(ranking,minimum=0.6):
    return {"passed":ranking["score"]>=minimum,"score":ranking["score"],"minimum":minimum}
