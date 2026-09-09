def validate_plan(plan):
    errors=[]
    if plan.get("status")!="READY": errors.append("PLAN_NOT_READY")
    for b in plan.get("blocks",[]):
        if not b.get("objective"): errors.append("BLOCK_WITHOUT_OBJECTIVE")
        if b["type"]!="ORIENTATION" and not b.get("evidence_ids"):
            errors.append("UNGROUNDED_BLOCK:"+b["type"])
    return {"valid":not errors,"errors":errors}
