def event_envelope(event_id, event_type, payload,
                  source=None, timestamp=None, headers=None):
    if not event_id or not event_type:
        raise ValueError("INVALID_EVENT_ENVELOPE")
    return {"event_id":event_id,"event_type":event_type,
            "payload":payload,"source":source,
            "timestamp":timestamp,"headers":headers or {}}

def valid(record):
    return bool(record["event_id"] and record["event_type"])
