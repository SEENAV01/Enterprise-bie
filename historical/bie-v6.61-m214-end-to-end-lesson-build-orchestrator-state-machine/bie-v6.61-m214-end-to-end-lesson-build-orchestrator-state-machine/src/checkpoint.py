def checkpoint(checkpoint_id, job_id, state,
               artifact_refs=None, event_index=0):
    return {"checkpoint_id":checkpoint_id,"job_id":job_id,
            "state":state,"artifact_refs":artifact_refs or [],
            "event_index":event_index}

def resumable(c):
    return bool(c["checkpoint_id"] and c["job_id"] and c["state"])
