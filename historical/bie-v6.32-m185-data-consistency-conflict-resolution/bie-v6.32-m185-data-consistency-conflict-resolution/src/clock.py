def logical_clock(node_id, counter=0):
    if counter < 0:
        raise ValueError("INVALID_COUNTER")
    return {"node_id":node_id,"counter":counter}

def tick(clock):
    out=dict(clock); out["counter"] += 1; return out

def compare(a,b):
    if a["counter"] < b["counter"]: return -1
    if a["counter"] > b["counter"]: return 1
    return 0
