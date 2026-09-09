def policy(policy_id,version,rules=None,
           default_effect="DENY",metadata=None):
    return {"policy_id":policy_id,"version":version,
            "rules":rules or [],"default_effect":default_effect,
            "metadata":metadata or {}}

def rule(rule_id,action,resource,effect="ALLOW",
         conditions=None,approval=None):
    return {"rule_id":rule_id,"action":action,
            "resource":resource,"effect":effect,
            "conditions":conditions or {},
            "approval":approval or {}}
