def lesson_job(job_id, source_ref, requested_output,
               state="INGESTED", metadata=None):
    return {"job_id":job_id,"source_ref":source_ref,
            "requested_output":requested_output,"state":state,
            "metadata":metadata or {}}

def valid(j):
    return bool(j["job_id"] and j["source_ref"] and j["requested_output"])
