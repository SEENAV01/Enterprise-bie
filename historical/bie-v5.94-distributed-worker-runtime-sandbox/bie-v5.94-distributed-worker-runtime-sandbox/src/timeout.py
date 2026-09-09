def timeout_policy(timeout_seconds,
                  grace_seconds=0):
    return {"timeout_seconds":timeout_seconds,
            "grace_seconds":grace_seconds}

def timed_out(started_at,now,policy):
    return now-started_at>policy["timeout_seconds"]
