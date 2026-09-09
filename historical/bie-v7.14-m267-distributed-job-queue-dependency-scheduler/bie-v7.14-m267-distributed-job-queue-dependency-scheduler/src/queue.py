def enqueue(queue, job, priority=50):
    job={**job,"priority":priority,"status":"QUEUED"}
    queue.append(job)
    queue.sort(key=lambda x:(-x["priority"],x["job_id"]))
    return job

def dequeue(queue, concurrency=1, active=0):
    if active>=concurrency or not queue:return None
    job=queue.pop(0); job["status"]="DISPATCHED"; return job
