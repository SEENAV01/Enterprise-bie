def timezone_policy(name="UTC", dst_policy="STANDARD"):
    if not name:
        raise ValueError("INVALID_TIMEZONE")
    if dst_policy not in {"STANDARD","SKIP","DUPLICATE","REJECT"}:
        raise ValueError("INVALID_DST_POLICY")
    return {"timezone":name,"dst_policy":dst_policy}

def valid(record):
    return bool(record["timezone"])
