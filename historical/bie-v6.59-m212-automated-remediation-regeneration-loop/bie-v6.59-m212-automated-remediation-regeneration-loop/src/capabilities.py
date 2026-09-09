def remediation_capabilities():
    return {
        "failure_classification":True,
        "root_cause_diagnosis":True,
        "targeted_remediation":True,
        "impact_analysis":True,
        "partial_regeneration":True,
        "rerender_scope_control":True,
        "re_qa_cycle":True,
        "regeneration_guard":True,
        "provenance":True,
        "verification_gate":True
    }
