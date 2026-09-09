def task_requirements(task_type,capability,
                     min_quality=0.0,max_cost=None,
                     max_latency_ms=None,
                     min_reliability=0.0,
                     context_tokens=0):
    return {"task_type":task_type,"capability":capability,
            "min_quality":min_quality,"max_cost":max_cost,
            "max_latency_ms":max_latency_ms,
            "min_reliability":min_reliability,
            "context_tokens":context_tokens}
