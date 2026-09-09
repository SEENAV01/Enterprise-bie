def diagnose(concept_id,results):
    xs=[r for r in results if r["concept_id"]==concept_id]
    score=sum(r["score"] for r in xs)/len(xs) if xs else 0
    if score>=0.85: status="MASTERED"
    elif score>=0.65: status="DEVELOPING"
    else: status="GAP"
    return {"concept_id":concept_id,"mastery":round(score,3),"status":status,
            "needs_review":status!="MASTERED"}

def diagnostic_report(results):
    concepts=sorted({r["concept_id"] for r in results})
    return [diagnose(c,results) for c in concepts]
