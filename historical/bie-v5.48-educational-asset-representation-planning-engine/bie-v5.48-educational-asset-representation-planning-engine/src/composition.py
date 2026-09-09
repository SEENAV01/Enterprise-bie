def composition_plan(plan_id,parts=None,sequence=None,
                     synchronization=None):
    return {"plan_id":plan_id,"parts":parts or [],
            "sequence":sequence or [],
            "synchronization":synchronization or {}}
