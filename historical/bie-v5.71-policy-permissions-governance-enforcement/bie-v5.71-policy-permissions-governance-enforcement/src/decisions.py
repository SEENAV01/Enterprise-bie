def evaluate(request,principal,policy):
    for r in policy.get("rules",[]):
        if r.get("action")==request.get("action") and r.get("resource")==request.get("resource"):
            if r.get("conditions") and not all(
                request.get("context",{}).get(k)==v
                for k,v in r["conditions"].items()):
                continue
            approval=r.get("approval",{})
            if approval.get("required"):
                return {"decision":"ESCALATE",
                        "reason":"APPROVAL_REQUIRED","rule_id":r["rule_id"]}
            return {"decision":r.get("effect","DENY"),
                    "reason":"POLICY_RULE","rule_id":r["rule_id"]}
    return {"decision":policy.get("default_effect","DENY"),
            "reason":"DEFAULT_POLICY"}

def enforce_capability(request,principal):
    return {"allowed":request.get("capability") in principal.get("capabilities",[])}
