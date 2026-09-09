def diagnostic_context(trace_id,
                       correlation_id=None,
                       workflow_id=None,
                       task_id=None,
                       extra=None):
    return {"trace_id":trace_id,
            "correlation_id":correlation_id,
            "workflow_id":workflow_id,
            "task_id":task_id,
            "extra":extra or {}}
