def principal(principal_id, kind="USER", attributes=None):
    if kind not in {"USER","SERVICE","GROUP"}:
        raise ValueError("INVALID_PRINCIPAL_KIND")
    return {"principal_id":principal_id,"kind":kind,
            "attributes":attributes or {},"status":"ACTIVE"}

def active(record):
    return record["status"]=="ACTIVE"
