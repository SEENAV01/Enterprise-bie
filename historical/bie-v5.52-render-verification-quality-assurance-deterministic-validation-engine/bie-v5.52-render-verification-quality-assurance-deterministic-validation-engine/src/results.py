def check_result(check_id,status,score=None,evidence=None,
                message=None,metrics=None):
    return {"check_id":check_id,"status":status,"score":score,
            "evidence":evidence or [],"message":message,
            "metrics":metrics or {}}

def aggregate_status(results):
    statuses=[r.get("status") for r in results]
    if any(s=="FAIL" for s in statuses): return "FAIL"
    if any(s=="NEEDS_REVIEW" for s in statuses): return "NEEDS_REVIEW"
    return "PASS"
