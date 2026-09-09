def task_result(task_id,worker_id,status,
                outputs=None,error=None,metrics=None):
    return {"task_id":task_id,"worker_id":worker_id,
            "status":status,"outputs":outputs or [],
            "error":error,"metrics":metrics or {}}

def successful(result):
    return result.get("status")=="SUCCEEDED"
