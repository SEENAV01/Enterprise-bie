def access_constraint(dataset_id,principal_scope,
                     allowed_actions=None):
    return {"dataset_id":dataset_id,
            "principal_scope":principal_scope,
            "allowed_actions":allowed_actions or []}

def can_access(constraint,scope,action):
    return (constraint.get("principal_scope")==scope and
            action in set(constraint.get("allowed_actions",[])))
