def retention_policy(policy_id,
                    duration_seconds,
                    action="DELETE",
                    legal_basis=None):
    return {"policy_id":policy_id,
            "duration_seconds":duration_seconds,
            "action":action,
            "legal_basis":legal_basis}

def expired(created_at,now,policy):
    return now-created_at >= policy["duration_seconds"]
