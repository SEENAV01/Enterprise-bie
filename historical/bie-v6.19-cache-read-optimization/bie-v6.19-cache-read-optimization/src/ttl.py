def ttl_policy(cache_name,
               ttl_seconds,
               stale_while_revalidate=0):
    if ttl_seconds < 0 or stale_while_revalidate < 0:
        raise ValueError("INVALID_TTL")
    return {"cache":cache_name,
            "ttl_seconds":ttl_seconds,
            "stale_while_revalidate":
                stale_while_revalidate}

def expired(created_at,now,ttl_seconds):
    return now >= created_at + ttl_seconds
