def adaptation_step(step_id,condition,action,target_refs=None,
                   priority=0.5):
    return {"step_id":step_id,"condition":condition,
            "action":action,"target_refs":target_refs or [],
            "priority":priority}

def adaptation_plan(plan_id,diagnosis_refs=None,steps=None,
                    reassessment=None):
    return {"plan_id":plan_id,"diagnosis_refs":diagnosis_refs or [],
            "steps":steps or [],"reassessment":reassessment}
