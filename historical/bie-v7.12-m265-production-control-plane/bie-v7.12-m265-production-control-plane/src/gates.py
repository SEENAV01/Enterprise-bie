def deployment_gate(qa_passed, approvals, artifact_verified, observability_valid):
    errors=[]
    if not qa_passed: errors.append("QA_NOT_PASSED")
    if not approvals: errors.append("RELEASE_APPROVAL_MISSING")
    if not artifact_verified: errors.append("ARTIFACT_NOT_VERIFIED")
    if not observability_valid: errors.append("OBSERVABILITY_INVALID")
    return {"release":not errors,"errors":errors}

def release_gate(run, gate):
    return {"allowed":run["state"]=="AWAITING_APPROVAL" and gate["release"],
            "errors":[] if run["state"]=="AWAITING_APPROVAL" and gate["release"]
                    else (gate["errors"] or ["RUN_NOT_AWAITING_APPROVAL"])}
