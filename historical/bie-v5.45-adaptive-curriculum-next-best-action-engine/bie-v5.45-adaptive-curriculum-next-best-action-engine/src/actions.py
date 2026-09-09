def learning_action(action_id,action_type,target_refs=None,
                   objective_refs=None,reason=None,estimated_value=None,
                   prerequisites=None,constraints=None):
    return {"action_id":action_id,"action_type":action_type,
            "target_refs":target_refs or [],
            "objective_refs":objective_refs or [],
            "reason":reason,"estimated_value":estimated_value,
            "prerequisites":prerequisites or [],
            "constraints":constraints or {}}

def action_types():
    return ["NEW_CONCEPT","PREREQUISITE_REVIEW","REMEDIATE",
            "PRACTICE","ASSESS","REVIEW","SKIP","REPRESENTATION_CHANGE",
            "ENRICH","REFLECT"]
