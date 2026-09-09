def registry_entry(name,version,
                  status="CURRENT"):
    return {"name":name,"version":version,"status":status}

def compatible(current,requested):
    return current.get("name")==requested.get("name")
