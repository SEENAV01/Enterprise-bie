def quorum(members, required=None):
    n=len(members)
    required=required if required is not None else n//2+1
    if required<1 or required>n:
        raise ValueError("INVALID_QUORUM")
    return {"members":members,"required":required}

def reached(record, acknowledgements):
    return len(set(acknowledgements)&set(record["members"]))>=record["required"]
