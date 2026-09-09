def task(task_id,operation,inputs=None,
         outputs=None,retry_policy=None,
         idempotency_key=None):
    return {"task_id":task_id,"operation":operation,
            "inputs":inputs or [],"outputs":outputs or [],
            "retry_policy":retry_policy or {},
            "idempotency_key":idempotency_key}

def task_state(task_id,status="PENDING",attempt=0,
               checkpoint=None,error=None):
    return {"task_id":task_id,"status":status,
            "attempt":attempt,"checkpoint":checkpoint,
            "error":error}
