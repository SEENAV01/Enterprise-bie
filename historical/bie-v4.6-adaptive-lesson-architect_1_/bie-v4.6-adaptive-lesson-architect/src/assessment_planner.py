def assessment_for(unit):
    mode=unit.get("teaching_mode","EXPLAIN")
    if mode=="DERIVE_STEP_BY_STEP":
        return ["REPRODUCE_DERIVATION","FIND_MISSING_STEP"]
    if mode=="SHOW_APPLICATION":
        return ["APPLY_TO_NEW_CONTEXT"]
    if mode=="EXPLAIN_WITH_CAUSAL_MODEL":
        return ["EXPLAIN_CAUSE_EFFECT"]
    if mode=="COMPARE":
        return ["DISTINGUISH_CASES"]
    return ["RECALL","EXPLAIN_IN_OWN_WORDS"]
