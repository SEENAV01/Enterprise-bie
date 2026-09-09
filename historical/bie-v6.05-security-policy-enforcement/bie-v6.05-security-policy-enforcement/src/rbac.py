def role(name,permissions=None):
    return {"name":name,
            "permissions":permissions or []}

def role_allows(roles,action,resource):
    for r in roles:
        for p in r.get("permissions",[]):
            if (p.get("action")==action and
                p.get("resource")==resource and
                p.get("effect","ALLOW")=="ALLOW"):
                return True
    return False
