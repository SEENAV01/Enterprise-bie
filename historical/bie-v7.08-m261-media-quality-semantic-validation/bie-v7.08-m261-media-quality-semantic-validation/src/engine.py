def aggregate(results):
    hard=[]
    for name,result in results.items():
        if not result.get("valid",False): hard.extend([f"{name}:{e}" for e in result.get("errors",[])])
    total=len(results); passed=sum(1 for r in results.values() if r.get("valid",False))
    return {"valid":not hard,"score":round(100*passed/max(1,total),2),
            "passed":passed,"checks":total,"errors":hard}

def repair_candidates(results):
    return [{"domain":k,"errors":v.get("errors",[])}
            for k,v in results.items() if not v.get("valid",False)]
