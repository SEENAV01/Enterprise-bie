from dispatch import eligible_workers,dispatch

def compile_dispatch(task_id,workers,
                     requirements=None,resources=None):
    candidates=eligible_workers(workers,
                                requirements,resources)
    selected=candidates[0]["worker_id"] if candidates else None
    return {"schema_version":"5.94",
            "candidates":[w["worker_id"] for w in candidates],
            "dispatch":dispatch(task_id,selected,
                                requirements,resources)
              if selected else None,
            "quality_gate":{"valid":True,"errors":[]}}
