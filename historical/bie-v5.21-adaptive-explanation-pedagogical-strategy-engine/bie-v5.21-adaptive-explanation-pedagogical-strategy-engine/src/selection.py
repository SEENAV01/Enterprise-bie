def select_strategy(learner,concept,difficulty_level,
                   misconception_risk=0.0):
    mastery=learner.get("mastery",{}).get(concept,0)
    if mastery<0.35: depth="FOUNDATIONAL"
    elif mastery<0.7: depth="STANDARD"
    else: depth="COMPACT_PLUS_EXTENSION"
    visual=learner.get("preferences",{}).get("visual_modality","BEST_FIT")
    intervention="TARGETED" if misconception_risk>=0.75 else "NORMAL"
    return {"explanation_depth":depth,"visual_modality":visual,
            "intervention":intervention,
            "practice_density":"HIGH" if mastery<0.5 else "ADAPTIVE",
            "pacing":"CONTENT_DRIVEN"}
