def config(name,version,
           values=None,scope=None,
           status="DRAFT"):
    return {"name":name,"version":version,
            "values":values or {},
            "scope":scope,
            "status":status}

def activate(record):
    out=dict(record); out["status"]="ACTIVE"; return out

def deactivate(record):
    out=dict(record); out["status"]="INACTIVE"; return out
