def dead_letter(message_id,
               original_queue,
               attempts,reason,
               payload_ref=None):
    return {"message_id":message_id,
            "original_queue":original_queue,
            "attempts":attempts,
            "reason":reason,
            "payload_ref":payload_ref,
            "status":"PENDING"}

def requeue(record):
    out=dict(record)
    out["status"]="REQUEUED"
    return out
