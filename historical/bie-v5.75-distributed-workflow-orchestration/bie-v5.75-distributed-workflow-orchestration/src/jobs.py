def job(job_id,kind,payload=None,depends_on=None,
        priority=0,max_attempts=3):
    return {"job_id":job_id,"kind":kind,"payload":payload or {},
            "depends_on":depends_on or [],"priority":priority,
            "max_attempts":max_attempts,"attempts":0,"status":"PENDING"}

def runnable(job_record,completed):
    return (job_record.get("status")=="PENDING" and
            all(x in completed for x in job_record.get("depends_on",[])))
