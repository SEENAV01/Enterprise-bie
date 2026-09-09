def outbox_event(event_id,aggregate_id,
                 event_type,payload_hash):
    return {"event_id":event_id,
            "aggregate_id":aggregate_id,
            "event_type":event_type,
            "payload_hash":payload_hash,
            "status":"PENDING"}

def publish(record):
    out=dict(record); out["status"]="PUBLISHED"; return out
