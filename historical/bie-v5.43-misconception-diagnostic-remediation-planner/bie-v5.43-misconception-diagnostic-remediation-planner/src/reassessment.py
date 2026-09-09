def reassessment_plan(item_type,target_objective,
                     target_diagnosis=None,difficulty_delta=0,
                     evidence_goal=None):
    return {"item_type":item_type,"target_objective":target_objective,
            "target_diagnosis":target_diagnosis,
            "difficulty_delta":difficulty_delta,
            "evidence_goal":evidence_goal}
