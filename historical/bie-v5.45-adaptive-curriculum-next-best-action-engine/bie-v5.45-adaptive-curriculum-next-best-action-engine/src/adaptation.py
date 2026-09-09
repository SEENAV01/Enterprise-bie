def adaptation_decision(decision_id,selected_action=None,
                       alternatives=None,reason=None,evidence_refs=None):
    return {"decision_id":decision_id,
            "selected_action":selected_action,
            "alternatives":alternatives or [],
            "reason":reason,
            "evidence_refs":evidence_refs or []}
