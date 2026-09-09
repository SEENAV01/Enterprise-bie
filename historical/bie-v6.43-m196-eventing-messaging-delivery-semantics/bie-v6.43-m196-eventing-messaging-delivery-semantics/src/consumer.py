def consumer(consumer_id, group_id,
            concurrency=1, ack_mode="EXPLICIT"):
    if concurrency < 1:
        raise ValueError("INVALID_CONCURRENCY")
    if ack_mode not in {"AUTO","EXPLICIT","BATCH"}:
        raise ValueError("INVALID_ACK_MODE")
    return {"consumer_id":consumer_id,"group_id":group_id,
            "concurrency":concurrency,"ack_mode":ack_mode,
            "status":"ACTIVE"}

def active(record):
    return record["status"]=="ACTIVE"
