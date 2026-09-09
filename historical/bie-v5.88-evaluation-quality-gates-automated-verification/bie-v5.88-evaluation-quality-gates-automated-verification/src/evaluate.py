from rubric import weighted_score

def evaluation(artifact_id,results,confidence=1.0):
    score=weighted_score(results)
    return {"artifact_id":artifact_id,
            "criteria":results,
            "score":score,
            "confidence":confidence,
            "passed":all(r["passed"] for r in results)}

def regression(current,baseline,tolerance=0.0):
    delta=current["score"]-baseline["score"]
    return {"delta":delta,
            "regressed":delta < -abs(tolerance)}
