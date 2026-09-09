from approval import valid_decision
from override import override_allowed
from dual_control import dual_control

def compile_review(review_case,decision=None,
                   override=None,dual_decisions=None):
    errors=[]
    if decision is not None and not valid_decision(decision):
        errors.append("INVALID_DECISION")
    if override is not None and not override_allowed(override):
        errors.append("INVALID_OVERRIDE")
    if dual_decisions is not None and not dual_control(dual_decisions):
        errors.append("DUAL_CONTROL_NOT_SATISFIED")
    return {"schema_version":"5.80",
            "review":review_case,
            "decision":decision,
            "override":override,
            "quality_gate":{"valid":not errors,"errors":errors}}
