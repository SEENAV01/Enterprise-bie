def capabilities():
    return {
        "distributed_job_queue":True,
        "worker_registry":True,
        "resource_allocation":True,
        "attempt_tracking":True,
        "retry_policy":True,
        "checkpoint_resume":True,
        "worker_failure_recovery":True,
        "result_aggregation":True
    }
