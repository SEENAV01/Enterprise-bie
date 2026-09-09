def timeline(scenes):
    total=sum((s.get("duration_sec") or 0) for s in scenes)
    return {"total_duration_sec":total,"scene_count":len(scenes)}

def validate_continuity(scenes):
    orders=[s["order"] for s in scenes]
    return orders == sorted(orders) and len(orders) == len(set(orders))
