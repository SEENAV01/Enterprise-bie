def checkpoint(job_id,checkpoint_id,progress,
               artifact_refs=None,state_digest=None):
    return {"job_id":job_id,"checkpoint_id":checkpoint_id,
            "progress":progress,
            "artifact_refs":artifact_refs or [],
            "state_digest":state_digest}

def latest_checkpoint(checkpoints,job_id):
    matches=[x for x in checkpoints if x.get("job_id")==job_id]
    return matches[-1] if matches else None
