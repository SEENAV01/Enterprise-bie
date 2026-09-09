def dispatch(job_id,schedule_id,
             fire_time,leader_term):
    return {"job_id":job_id,
            "schedule_id":schedule_id,
            "fire_time":fire_time,
            "leader_term":leader_term,
            "status":"READY"}

def dispatched(record):
    out=dict(record); out["status"]="DISPATCHED"; return out
