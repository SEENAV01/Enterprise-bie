def schedule(workflow_id,task_ids,
            concurrency=1):
    return {"workflow_id":workflow_id,
            "task_ids":task_ids,
            "concurrency":max(1,concurrency)}

def batches(task_ids,concurrency):
    c=max(1,concurrency)
    return [task_ids[i:i+c] for i in range(0,len(task_ids),c)]
