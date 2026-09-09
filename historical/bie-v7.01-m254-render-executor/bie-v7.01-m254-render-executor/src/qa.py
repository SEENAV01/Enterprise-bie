def render_qa(result, expected_output):
    errors=[]
    if result.get("output")!=expected_output: errors.append("OUTPUT_PATH_MISMATCH")
    if result.get("status")!="RENDERED": errors.append("RENDER_STATUS_INVALID")
    return {"valid":not errors,"errors":errors}

def release_gate(build, render, artifact, qa):
    checks=[build["valid"],render["valid"],artifact["valid"],qa["valid"]]
    return {"valid":all(checks),"errors":[] if all(checks) else ["RENDER_RELEASE_BLOCKED"]}
