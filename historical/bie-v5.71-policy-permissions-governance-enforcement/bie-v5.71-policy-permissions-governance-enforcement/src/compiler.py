from decisions import evaluate,enforce_capability
from risk import risk_classification

def authorize(request,principal,policy):
    capability=enforce_capability(request,principal)
    if not capability["allowed"]:
        return {"schema_version":"5.71","decision":"DENY",
                "reason":"CAPABILITY_MISSING","risk":risk_classification(request.get("action"))}
    decision=evaluate(request,principal,policy)
    return {"schema_version":"5.71","risk":risk_classification(request.get("action")),
            **decision}
