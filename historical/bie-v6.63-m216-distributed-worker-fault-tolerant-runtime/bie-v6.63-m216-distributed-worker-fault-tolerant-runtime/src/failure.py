def worker_failure(worker_id,reason,affected_job_ids=None,
                  recoverable=True):
    return {"worker_id":worker_id,"reason":reason,
            "affected_job_ids":affected_job_ids or [],
            "recoverable":recoverable}

def recovery_action(failure):
    return "REQUEUE_AFFECTED_JOBS" if failure["recoverable"] else "ESCALATE"
