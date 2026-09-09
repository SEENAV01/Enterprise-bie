def security_event(event_id,
                   event_type,subject_id,
                   service,decision,
                   resource=None,reason=None):
    return {"event_id":event_id,
            "event_type":event_type,
            "subject_id":subject_id,
            "service":service,
            "decision":decision,
            "resource":resource,
            "reason":reason}

def denied(record):
    return record["decision"]=="DENY"
