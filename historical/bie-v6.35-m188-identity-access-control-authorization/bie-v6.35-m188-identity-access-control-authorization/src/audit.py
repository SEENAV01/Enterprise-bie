def audit_event(event_id, principal_id,
               action, resource, decision, reason):
    return {"event_id":event_id,
            "principal_id":principal_id,
            "action":action,
            "resource":resource,
            "decision":decision,
            "reason":reason}

def denied(record):
    return record["decision"]=="DENY"
