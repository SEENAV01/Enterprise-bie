def aggregate(job_results):
    if any(r["status"]=="FAILED" for r in job_results):
        status="FAILED"
    elif job_results and all(r["status"]=="SUCCEEDED" for r in job_results):
        status="SUCCEEDED"
    else:
        status="RUNNING"
    return {"status":status,"results":job_results}
