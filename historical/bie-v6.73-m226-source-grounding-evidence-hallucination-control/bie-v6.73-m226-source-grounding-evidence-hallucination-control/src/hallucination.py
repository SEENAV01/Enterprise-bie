def risk(claim,grounding,relevance_threshold=0.5):
    if not grounding["grounded"]: return {"level":"HIGH","score":1.0}
    score=max(0.0,1-grounding["best_relevance"])
    level="LOW" if score<0.3 else ("MEDIUM" if score<0.6 else "HIGH")
    return {"level":level,"score":score}
def gate(risks,max_level="MEDIUM"):
    order={"LOW":0,"MEDIUM":1,"HIGH":2}
    return {"passed":all(order[r["level"]]<=order[max_level] for r in risks),
            "risks":risks}
