def quota(tenant_id,resource,
          limit,unit,period=None):
    return {"tenant_id":tenant_id,
            "resource":resource,
            "limit":limit,
            "unit":unit,
            "period":period}

def within(quota_record,usage):
    return usage <= quota_record["limit"]
