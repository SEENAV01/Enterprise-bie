def quality_gate(scene_results,render_results=None,reviews=None):
    errors=[e for r in scene_results for e in r.get("errors",[])]
    errors += [e for r in (render_results or []) for e in r.get("errors",[])]
    pending=[r for r in (reviews or []) if r.get("required") and r.get("status")=="PENDING"]
    rejected=[r for r in (reviews or []) if r.get("decision")=="REJECT"]
    if pending: errors.append("HUMAN_REVIEW_PENDING")
    if rejected: errors.append("HUMAN_REVIEW_REJECTED")
    return {"passed":not errors,"errors":errors}
