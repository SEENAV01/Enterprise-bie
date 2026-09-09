def verification(check_id, job_id, state, status,
                 evidence_ids=None, final_artifact=None):
    if status not in {"PASS","FAIL","REVIEW"}:
        raise ValueError("INVALID_VERIFICATION_STATUS")
    return {"check_id":check_id,"job_id":job_id,"state":state,
            "status":status,"evidence_ids":evidence_ids or [],
            "final_artifact":final_artifact}

def passed(v):
    return v["status"]=="PASS" and v["state"]=="VERIFIED"
