def handling_policy(classification,
                   allowed_locations=None,
                   allowed_processors=None):
    return {"classification":classification,
            "allowed_locations":allowed_locations or [],
            "allowed_processors":allowed_processors or []}

def location_allowed(policy, location):
    return not policy["allowed_locations"] or location in policy["allowed_locations"]
