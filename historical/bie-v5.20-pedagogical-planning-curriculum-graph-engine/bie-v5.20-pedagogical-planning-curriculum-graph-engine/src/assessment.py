def assessment_target(target_id,concept_id,skill,success_criteria,
                      difficulty=None):
    return {"target_id":target_id,"concept_id":concept_id,
            "skill":skill,"success_criteria":success_criteria,
            "difficulty":difficulty}
