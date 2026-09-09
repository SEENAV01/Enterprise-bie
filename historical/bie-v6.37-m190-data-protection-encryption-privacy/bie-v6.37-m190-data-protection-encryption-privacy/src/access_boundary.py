def access_boundary(principal_id,
                    data_classification,
                    allowed_actions=None):
    return {"principal_id":principal_id,
            "data_classification":data_classification,
            "allowed_actions":allowed_actions or []}

def action_allowed(boundary, action):
    return action in boundary["allowed_actions"]
