def legal_hold(object_id,
                active=False,
                reason=None):
    return {"object_id":object_id,
            "active":active,
            "reason":reason}

def protected(record):
    return record["active"]
