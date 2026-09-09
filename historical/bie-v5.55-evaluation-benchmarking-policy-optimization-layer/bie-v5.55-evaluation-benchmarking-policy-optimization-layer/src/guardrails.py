def optimization_guard(policy_change,
                      max_scope="LOCAL",
                      require_evidence=True):
    scope=policy_change.get("scope","LOCAL")
    if scope!=max_scope:
        return {"allowed":False,"reason":"SCOPE_EXCEEDED"}
    if require_evidence and not policy_change.get("evidence_refs"):
        return {"allowed":False,"reason":"EVIDENCE_REQUIRED"}
    return {"allowed":True,"reason":None}

def approval_gate(change,approved=False):
    if change.get("approval_required",True) and not approved:
        return {"status":"PENDING_APPROVAL"}
    return {"status":"APPROVED"}
