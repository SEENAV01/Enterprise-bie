def publish(event,topic_id,partition=0,offset=None):
    return {"topic_id":topic_id,
            "partition":partition,
            "offset":offset,
            "event":event,"status":"PUBLISHED"}

def delivery(message,subscription_id,attempt=1):
    return {"message":message,
            "subscription_id":subscription_id,
            "attempt":attempt,
            "status":"DELIVERED"}
