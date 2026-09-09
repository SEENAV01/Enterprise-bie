def compile_experience(contract,interactions,feedback_rules=None,
                       controls=None,adaptive_hooks=None):
    ids={x["interaction_id"] for x in interactions}
    missing=[x for x in contract.get("interaction_refs",[]) if x not in ids]
    errors=["MISSING_INTERACTION_REFERENCE"] if missing else []
    return {"schema_version":"5.35",
            "lesson_contract":contract,
            "interactions":interactions,
            "feedback_rules":feedback_rules or [],
            "controls":controls or [],
            "adaptive_hooks":adaptive_hooks or [],
            "quality_gate":{"valid":not errors,"errors":errors}}
