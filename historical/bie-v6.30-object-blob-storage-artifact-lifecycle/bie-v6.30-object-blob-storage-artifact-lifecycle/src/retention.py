def retention(policy="NONE",
             retain_until=None):
    if policy not in {"NONE","TIME_BASED","INDEFINITE"}:
        raise ValueError("INVALID_RETENTION_POLICY")
    return {"policy":policy,
            "retain_until":retain_until}

def protected(record,now=None):
    return record["policy"]=="INDEFINITE" or (
        record["policy"]=="TIME_BASED" and
        now is not None and now < record["retain_until"])
