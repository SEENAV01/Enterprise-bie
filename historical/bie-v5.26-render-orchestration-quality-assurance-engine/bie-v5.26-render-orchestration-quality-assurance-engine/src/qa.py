def qa_report(render_result,asset_check=None,
              consistency_checks=None,frame_checks=None):
    checks=[]
    if asset_check: checks.append(asset_check)
    checks.extend(consistency_checks or [])
    checks.extend(frame_checks or [])
    errors=[]
    for c in checks:
        if not c.get("valid",False):
            errors.append(c.get("error","QA_CHECK_FAILED"))
            errors.extend(c.get("missing",[]))
    if render_result.get("status")!="SUCCEEDED":
        errors.append(render_result.get("error") or "RENDER_FAILED")
    return {"passed":not errors,"errors":errors}

def output_gate(qa):
    return {"release":bool(qa.get("passed")),"status":
            "RELEASE_READY" if qa.get("passed") else "BLOCKED"}
