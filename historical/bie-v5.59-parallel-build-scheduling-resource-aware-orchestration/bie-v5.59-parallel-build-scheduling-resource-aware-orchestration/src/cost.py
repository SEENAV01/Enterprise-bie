def estimate_cost(job,pricing=None):
    pricing=pricing or {}
    total=0
    for k,v in job.get("estimated",{}).items():
        if k in pricing: total += v*pricing[k]
    return total
