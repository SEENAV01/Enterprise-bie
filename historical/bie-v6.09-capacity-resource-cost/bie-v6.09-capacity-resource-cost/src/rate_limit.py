def rate_limit(name,requests,
               window_seconds,
               burst=None):
    return {"name":name,
            "requests":requests,
            "window_seconds":window_seconds,
            "burst":burst}

def allowed(limit,requests_seen):
    return requests_seen < limit["requests"]
