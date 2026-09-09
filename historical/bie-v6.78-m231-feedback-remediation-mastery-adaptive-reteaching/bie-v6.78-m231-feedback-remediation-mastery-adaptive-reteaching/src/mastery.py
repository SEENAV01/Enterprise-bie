def estimate_mastery(results):
    if not results:return {"mastery":0.0,"level":"UNKNOWN"}
    scores=[float(r.get("score",0)) for r in results]
    value=sum(scores)/len(scores)
    level="MASTERED" if value>=0.85 else ("DEVELOPING" if value>=0.60 else "NOT_MASTERED")
    return {"mastery":value,"level":level,"sample_count":len(scores)}

def concept_mastery(results):
    out={}
    for r in results:
        c=r["concept_id"]; out.setdefault(c,[]).append(r["score"])
    return {c:sum(v)/len(v) for c,v in out.items()}
