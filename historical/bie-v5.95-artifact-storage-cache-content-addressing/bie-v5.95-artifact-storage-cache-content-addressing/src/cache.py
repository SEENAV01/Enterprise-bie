def cache_key(operation,inputs,config=None):
    return {"operation":operation,"inputs":inputs,
            "config":config or {}}

def cache_entry(key,content_id,created_at,
                expires_at=None):
    return {"key":key,"content_id":content_id,
            "created_at":created_at,"expires_at":expires_at}

def cache_hit(entry,now=None):
    if entry is None: return False
    if entry.get("expires_at") is None: return True
    return now <= entry["expires_at"]
