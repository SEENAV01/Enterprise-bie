def checkpoint(workflow_id,completed_jobs,
               failed_jobs=None,state=None):
    return {"workflow_id":workflow_id,
            "completed_jobs":list(completed_jobs),
            "failed_jobs":list(failed_jobs or []),
            "state":state or {}}

def resumable(cp):
    return bool(cp.get("workflow_id"))
