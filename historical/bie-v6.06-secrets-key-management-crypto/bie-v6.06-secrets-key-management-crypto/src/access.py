def access_policy(material_id,
                 subjects=None,actions=None,
                 effect="DENY"):
    return {"material_id":material_id,
            "subjects":subjects or [],
            "actions":actions or [],
            "effect":effect}

def allowed(policy,subject,action):
    return (policy.get("effect")=="ALLOW" and
            subject in policy.get("subjects",[]) and
            action in policy.get("actions",[]))
