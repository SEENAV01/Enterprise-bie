def policy_version(policy_id, version, rules,
                   created_by=None, created_at=None):
    return {"policy_id":policy_id,"version":version,"rules":rules,
            "created_by":created_by,"created_at":created_at}

def next_version(current):
    return current+1
