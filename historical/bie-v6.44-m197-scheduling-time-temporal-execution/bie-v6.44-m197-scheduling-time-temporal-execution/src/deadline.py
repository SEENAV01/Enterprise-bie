def deadline(deadline_id, due_at, grace_period=None,
             policy="FAIL"):
    if policy not in {"FAIL","WARN","EXTEND"}:
        raise ValueError("INVALID_DEADLINE_POLICY")
    return {"deadline_id":deadline_id,"due_at":due_at,
            "grace_period":grace_period,"policy":policy}

def valid(record):
    return bool(record["due_at"])
