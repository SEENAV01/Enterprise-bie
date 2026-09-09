def inbox_record(message_id,consumer_id,
                 received_at):
    return {"message_id":message_id,
            "consumer_id":consumer_id,
            "received_at":received_at,
            "status":"RECEIVED"}

def already_processed(record):
    return record.get("status")=="PROCESSED"

def mark_processed(record):
    out=dict(record); out["status"]="PROCESSED"
    return out
