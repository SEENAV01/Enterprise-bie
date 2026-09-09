def temporal_state(resource_id, state,
                  effective_at, expires_at=None):
    return {"resource_id":resource_id,"state":state,
            "effective_at":effective_at,"expires_at":expires_at}

def active(record, timestamp):
    return timestamp >= record["effective_at"] and (
        record["expires_at"] is None or timestamp < record["expires_at"])
