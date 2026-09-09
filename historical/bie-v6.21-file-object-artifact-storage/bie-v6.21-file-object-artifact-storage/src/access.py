def object_access(object_id,
                 subject_id,
                 action,
                 tenant_id=None,
                 decision="ALLOW"):
    if action not in {"READ","WRITE","DELETE","LIST"}:
        raise ValueError("INVALID_OBJECT_ACTION")
    return {"object_id":object_id,
            "subject_id":subject_id,
            "action":action,
            "tenant_id":tenant_id,
            "decision":decision}

def allowed(record):
    return record["decision"]=="ALLOW"
