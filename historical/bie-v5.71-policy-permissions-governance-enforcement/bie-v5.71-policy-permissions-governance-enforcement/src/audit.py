def governance_decision_event(decision,request,principal):
    return {"event_type":"GOVERNANCE_DECISION",
            "principal":principal.get("principal_id"),
            "action":request.get("action"),
            "resource":request.get("resource"),
            "decision":decision.get("decision"),
            "reason":decision.get("reason"),
            "policy_ref":request.get("policy_ref")}
