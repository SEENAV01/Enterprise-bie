def capabilities():
    return {"dag_dependencies":True,"priority_queue":True,"retry_backoff":True,
            "idempotent_execution":True,"concurrency_limits":True,
            "critical_path_scheduling":True,"ready_job_detection":True}
