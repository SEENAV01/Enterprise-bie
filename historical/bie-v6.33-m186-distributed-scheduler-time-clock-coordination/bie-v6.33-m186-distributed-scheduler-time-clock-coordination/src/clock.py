def clock_sample(node_id, wall_time, monotonic_time,
                uncertainty_ms=0):
    if uncertainty_ms < 0:
        raise ValueError("INVALID_UNCERTAINTY")
    return {"node_id":node_id,"wall_time":wall_time,
            "monotonic_time":monotonic_time,
            "uncertainty_ms":uncertainty_ms}

def within_bound(sample,bound_ms):
    return sample["uncertainty_ms"] <= bound_ms
