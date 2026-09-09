def curriculum_gate(claim):
    if claim.get("properties",{}).get("status")=="REQUIRES_REVIEW":
        return {"allowed":False,"reason":"CLAIM_RECONCILIATION_REVIEW"}
    if claim.get("properties",{}).get("uncertainty") in ["CONFLICTED","UNSUPPORTED"]:
        return {"allowed":False,"reason":"CLAIM_UNCERTAIN"}
    return {"allowed":True,"reason":"CLAIM_CAN_BE_CONSUMED"}
