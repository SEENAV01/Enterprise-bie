def deadline_state(job,elapsed):
    d=job.get("deadline_seconds")
    if d is None: return "NO_DEADLINE"
    if elapsed>=d: return "MISSED"
    if elapsed>=0.8*d: return "AT_RISK"
    return "ON_TRACK"
