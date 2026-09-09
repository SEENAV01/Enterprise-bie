def create_job(job_id, payload, priority=50):
    return {"job_id":job_id,"payload":payload,"priority":priority,
            "status":"QUEUED","attempt":0,"checkpoint":None}

def enqueue(queue, job):
    queue.append(job); return sorted(queue,key=lambda x:(-x["priority"],x["job_id"]))

def dequeue(queue):
    return queue.pop(0) if queue else None
