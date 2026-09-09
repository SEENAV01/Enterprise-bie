def authorized(context,principal_record,resource,
               policy):
    if not context or context.get("principal_id") != principal_record.get("principal_id"):
        return False
    if not principal_record.get("active",False):
        return False
    if policy.get("effect")!="ALLOW":
        return False
    roles=set(principal_record.get("roles",[]))
    allowed=set(policy.get("allowed_roles",[]))
    if allowed and not roles.intersection(allowed):
        return False
    required=policy.get("required_scope")
    if required:
        scopes=set(principal_record.get("attributes",{}).get("scopes",[]))
        if required not in scopes:
            return False
    return True

def decision(context,principal_record,resource,policy):
    ok=authorized(context,principal_record,resource,policy)
    return {"allowed":ok,"reason":"ALLOW" if ok else "DENY"}
