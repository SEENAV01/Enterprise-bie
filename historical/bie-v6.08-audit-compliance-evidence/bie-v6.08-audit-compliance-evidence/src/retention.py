def evidence_retention(policy_id,
                      duration_seconds,
                      action="PRESERVE"):
    return {"policy_id":policy_id,
            "duration_seconds":duration_seconds,
            "action":action}

def retention_expired(created_at,now,policy):
    return now-created_at >= policy["duration_seconds"]
