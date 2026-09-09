def idempotency_key(task_id,key):
    return {"task_id":task_id,"key":key}

def same_execution(a,b):
    return a.get("key")==b.get("key")
