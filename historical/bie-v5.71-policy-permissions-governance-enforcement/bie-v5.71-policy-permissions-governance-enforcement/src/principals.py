def principal(principal_id,roles=None,capabilities=None,
              attributes=None):
    return {"principal_id":principal_id,"roles":roles or [],
            "capabilities":capabilities or [],
            "attributes":attributes or {}}

def has_capability(p,capability):
    return capability in set(p.get("capabilities",[]))
