def utilization(resource, used, capacity):
    if capacity <= 0:
        raise ValueError("INVALID_CAPACITY")
    return {"resource":resource,"used":used,
            "capacity":capacity,"ratio":used/capacity}

def saturated(record, threshold=1.0):
    return record["ratio"] >= threshold
