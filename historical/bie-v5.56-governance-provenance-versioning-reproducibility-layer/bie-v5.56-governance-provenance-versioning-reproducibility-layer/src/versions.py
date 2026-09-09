def version(ref,version_id,parent=None,content_hash=None,
           created_at=None,metadata=None):
    return {"ref":ref,"version_id":version_id,"parent":parent,
            "content_hash":content_hash,"created_at":created_at,
            "metadata":metadata or {}}

def version_pin(ref,version_id):
    return {"ref":ref,"version_id":version_id}

def resolve_pins(pins,registry):
    resolved={}
    for p in pins:
        key=(p["ref"],p["version_id"])
        if key not in registry:
            raise KeyError("UNRESOLVED_VERSION:"+str(key))
        resolved[p["ref"]]=registry[key]
    return resolved
