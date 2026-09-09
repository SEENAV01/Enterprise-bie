def checkpoint(checkpoint_id,job_id,attempt,
               stage,artifact_refs=None,state=None):
    return {"checkpoint_id":checkpoint_id,"job_id":job_id,
            "attempt":attempt,"stage":stage,
            "artifact_refs":artifact_refs or [],
            "state":state or {}}

def valid(c):
    return bool(c["checkpoint_id"] and c["job_id"] and c["stage"])
