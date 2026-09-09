def score_importance(item):
    p=item.get("properties",{})
    score=0.0
    score+=float(p.get("dependency_count",0))*0.15
    score+=float(p.get("downstream_count",0))*0.20
    score+=float(p.get("exam_relevance",0))*0.15
    score+=float(p.get("centrality",0))*0.20
    score+=float(p.get("practical_relevance",0))*0.15
    score+=float(p.get("misconception_risk",0))*0.15
    return min(1.0,score)

def classify_importance(score):
    if score>=.8:return "CORE"
    if score>=.55:return "IMPORTANT"
    if score>=.3:return "SUPPORTING"
    return "ENRICHMENT"
