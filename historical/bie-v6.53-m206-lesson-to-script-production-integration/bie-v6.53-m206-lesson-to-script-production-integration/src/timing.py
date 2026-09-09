def timing(blocks):
    total=sum((b.get("duration_sec") or 0) for b in blocks)
    return {"total_duration_sec":total,
            "block_count":len(blocks)}

def within_target(timing_result, target, tolerance=0.15):
    if target is None:
        return True
    return target*(1-tolerance) <= timing_result["total_duration_sec"] <= target*(1+tolerance)
