def signed_access(object_id,
                  action="GET",
                  expires_at=None,
                  constraints=None):
    if action not in {"GET","PUT","DELETE"}:
        raise ValueError("INVALID_SIGNED_ACTION")
    return {"object_id":object_id,
            "action":action,
            "expires_at":expires_at,
            "constraints":constraints or {}}

def valid(record,now):
    return record["expires_at"] is None or now < record["expires_at"]
