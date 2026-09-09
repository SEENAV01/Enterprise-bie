def outbox_record(record_id,aggregate_id,
                  event_type,payload,created_at):
    return {"record_id":record_id,
            "aggregate_id":aggregate_id,
            "event_type":event_type,
            "payload":payload,
            "created_at":created_at,
            "status":"PENDING"}

def mark_published(record):
    out=dict(record); out["status"]="PUBLISHED"
    return out
