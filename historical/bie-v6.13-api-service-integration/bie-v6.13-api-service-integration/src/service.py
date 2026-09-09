def service(name,version,
            base_path=None,owner=None):
    return {"name":name,"version":version,
            "base_path":base_path,"owner":owner,
            "status":"ACTIVE"}

def retire(record):
    out=dict(record); out["status"]="RETIRED"; return out
