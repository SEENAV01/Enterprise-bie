from trust import can_cross

def boundary_request(source_zone,target_zone,operation,credential=None):
    return {"source_zone":source_zone,"target_zone":target_zone,
            "operation":operation,"credential":credential}

def enforce_boundary(request,trust_policy):
    allowed=can_cross(request["source_zone"],request["target_zone"],trust_policy)
    return {"allowed":allowed,
            "reason":"TRUST_POLICY" if allowed else "TRUST_BOUNDARY_DENY"}
