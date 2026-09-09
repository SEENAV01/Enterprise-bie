def ttl_policy(ttl_seconds,
                refresh_on_read=False):
    if ttl_seconds is not None and ttl_seconds <= 0:
        raise ValueError("INVALID_TTL")
    return {"ttl_seconds":ttl_seconds,
            "refresh_on_read":refresh_on_read}

def expired(record,age_seconds):
    ttl=record["ttl_seconds"]
    return ttl is not None and age_seconds >= ttl
