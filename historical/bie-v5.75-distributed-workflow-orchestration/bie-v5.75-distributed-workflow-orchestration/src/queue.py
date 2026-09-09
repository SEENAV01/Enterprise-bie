def enqueue(queue,job_record):
    out=list(queue); out.append(job_record)
    out.sort(key=lambda j:-j.get("priority",0))
    return out

def dequeue(queue):
    if not queue: return None,list(queue)
    return queue[0],queue[1:]
