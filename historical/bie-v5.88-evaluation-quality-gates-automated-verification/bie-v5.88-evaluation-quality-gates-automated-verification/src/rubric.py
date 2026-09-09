def criterion(name,weight=1.0,threshold=0.0):
    return {"name":name,"weight":weight,"threshold":threshold}

def score_criterion(criterion,score,evidence=None):
    passed=score>=criterion["threshold"]
    return {"name":criterion["name"],"score":score,
            "weight":criterion["weight"],"passed":passed,
            "evidence":evidence or {}}

def weighted_score(results):
    total=sum(r["weight"] for r in results)
    return sum(r["score"]*r["weight"] for r in results)/total if total else 0.0
