def circuit(name,threshold=5,
            reset_after=30):
    return {"name":name,"threshold":threshold,
            "reset_after":reset_after,
            "state":"CLOSED","failures":0}

def record_failure(c):
    out=dict(c); out["failures"]=c.get("failures",0)+1
    if out["failures"]>=out["threshold"]:
        out["state"]="OPEN"
    return out

def allow(c):
    return c.get("state")!="OPEN"

def reset(c):
    out=dict(c); out["state"]="CLOSED"; out["failures"]=0
    return out
