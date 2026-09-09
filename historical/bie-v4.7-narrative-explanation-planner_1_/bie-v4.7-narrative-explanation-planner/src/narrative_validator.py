def validate(plan):
    errors=[]; warnings=[]
    if not plan.get("blocks"): errors.append("NO_BLOCKS")
    for e in plan.get("events",[]):
        if not e.get("source_ids") and e.get("type") in ["NARRATION","EQUATION","TEXT"]:
            warnings.append("UNGROUNDED_CONTENT_REQUIRES_REVIEW")
    if plan.get("timing_policy",{}).get("fixed_duration"):
        errors.append("FIXED_DURATION_FORBIDDEN")
    return {"valid":not errors,"errors":errors,"warnings":warnings}
