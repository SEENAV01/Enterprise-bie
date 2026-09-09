def concurrency_limit(resource,
                     max_concurrent,
                     queue_limit=0):
    return {"resource":resource,
            "max_concurrent":max_concurrent,
            "queue_limit":queue_limit}

def capacity_available(limit,active):
    return active < limit["max_concurrent"]
