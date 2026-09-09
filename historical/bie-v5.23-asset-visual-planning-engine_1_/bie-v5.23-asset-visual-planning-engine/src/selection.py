def select_modality(concept_type,objective_level,
                    learner_preference="BEST_FIT"):
    if learner_preference!="BEST_FIT":
        return learner_preference
    if concept_type in ("PROCESS","CHANGE","DYNAMIC"):
        return "2D_ANIMATION"
    if concept_type in ("DATA","COMPARISON"):
        return "CHART"
    if concept_type in ("SPATIAL","SYSTEM"):
        return "PROCESS_DIAGRAM"
    if concept_type in ("MATHEMATICAL","FORMULA"):
        return "EQUATION_BUILD"
    if objective_level in ("ANALYZE","APPLY"):
        return "SIMULATION"
    return "STATIC_DIAGRAM"
