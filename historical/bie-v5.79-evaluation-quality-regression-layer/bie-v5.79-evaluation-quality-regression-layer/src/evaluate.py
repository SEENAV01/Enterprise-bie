from rubric import weighted_score

def evaluate_case(case_id,scores,weights,threshold):
    score=weighted_score(scores,weights)
    return {"case_id":case_id,"scores":scores,
            "score":score,"passed":score>=threshold}

def evaluate_suite(results,threshold):
    scores=[r["score"] for r in results]
    avg=sum(scores)/len(scores) if scores else 0.0
    passed=all(r["passed"] for r in results)
    return {"average_score":avg,"passed":passed,
            "threshold":threshold,"cases":len(results)}
