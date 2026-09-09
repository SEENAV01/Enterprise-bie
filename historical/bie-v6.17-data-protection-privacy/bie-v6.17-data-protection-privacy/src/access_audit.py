def protected_access(event_id,
                    subject_id,resource,
                    purpose,decision,
                    tenant_id=None):
    return {"event_id":event_id,
            "subject_id":subject_id,
            "resource":resource,
            "purpose":purpose,
            "decision":decision,
            "tenant_id":tenant_id}

def allowed(record):
    return record["decision"]=="ALLOW"
