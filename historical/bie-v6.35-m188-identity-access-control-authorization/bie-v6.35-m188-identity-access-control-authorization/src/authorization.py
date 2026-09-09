def authorize(principal, permissions, action, resource):
    if principal["status"]!="ACTIVE":
        return {"decision":"DENY","reason":"INACTIVE_PRINCIPAL"}
    for p in permissions:
        if p["action"]==action and (p["resource"]==resource or p["resource"]=="*"):
            return {"decision":"ALLOW","reason":"MATCHED_PERMISSION"}
    return {"decision":"DENY","reason":"NO_MATCH"}

def allowed(decision):
    return decision["decision"]=="ALLOW"
