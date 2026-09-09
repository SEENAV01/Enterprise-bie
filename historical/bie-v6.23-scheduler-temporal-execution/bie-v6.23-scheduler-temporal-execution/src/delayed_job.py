def delayed_job(job_id,target_ref,
                run_at,attempt=0):
    return {"job_id":job_id,
            "target_ref":target_ref,
            "run_at":run_at,
            "attempt":attempt,
            "status":"SCHEDULED"}

def ready(record,now):
    return record["status"]=="SCHEDULED" and now >= record["run_at"]
