def enforcement_point(service,
                      policy_engine,
                      fail_closed=True):
    return {"service":service,
            "policy_engine":policy_engine,
            "fail_closed":fail_closed}

def enforce(point,decision):
    if decision in {"ALLOW","DENY"}:
        return decision
    return "DENY" if point["fail_closed"] else "ERROR"
