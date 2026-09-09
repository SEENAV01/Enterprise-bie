def acknowledgement(event_id, consumer_id,
                     status="ACKED", sequence=None):
    if status not in {"ACKED","NACKED","REQUEUED"}:
        raise ValueError("INVALID_ACK_STATUS")
    return {"event_id":event_id,"consumer_id":consumer_id,
            "status":status,"sequence":sequence}

def acknowledged(record):
    return record["status"]=="ACKED"
