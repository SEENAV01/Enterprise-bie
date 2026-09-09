def quota(quota_id, subject, resource,
          limit, period=None, burst=None):
    if limit < 0:
        raise ValueError("INVALID_QUOTA_LIMIT")
    return {"quota_id":quota_id,"subject":subject,
            "resource":resource,"limit":limit,
            "period":period,"burst":burst,"status":"ACTIVE"}

def within_limit(record, usage):
    return usage <= record["limit"] + (record["burst"] or 0)
