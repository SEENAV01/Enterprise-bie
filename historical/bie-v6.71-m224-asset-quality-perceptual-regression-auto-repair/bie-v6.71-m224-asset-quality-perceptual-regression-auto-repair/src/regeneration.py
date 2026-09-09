def regeneration_policy(attempt,max_attempts=2):
    return {"attempt":attempt,"max_attempts":max_attempts,
            "allowed":attempt<max_attempts}

def next_action(repair,policy):
    if not repair["regenerate"]: return "ACCEPT"
    return "REGENERATE" if policy["allowed"] else "ESCALATE"
