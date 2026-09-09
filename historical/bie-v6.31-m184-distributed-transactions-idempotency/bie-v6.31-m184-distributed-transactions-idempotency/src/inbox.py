def inbox_event(event_id, payload_hash,
                received_at=None):
    return {"event_id":event_id,
            "payload_hash":payload_hash,
            "received_at":received_at,
            "status":"RECEIVED"}

def consume(record):
    out=dict(record); out["status"]="CONSUMED"; return out
