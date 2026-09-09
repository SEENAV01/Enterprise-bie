ZONES={"UNTRUSTED","SANDBOX","WORKER","PRODUCTION","PROTECTED"}

def trust_zone(name,allowed_outbound=None,
               allowed_inbound=None):
    if name not in ZONES:
        raise ValueError("UNKNOWN_TRUST_ZONE")
    return {"name":name,
            "allowed_outbound":allowed_outbound or [],
            "allowed_inbound":allowed_inbound or []}

def can_cross(source,target,policy):
    return target in policy.get(source,{}).get("allowed_outbound",[])
