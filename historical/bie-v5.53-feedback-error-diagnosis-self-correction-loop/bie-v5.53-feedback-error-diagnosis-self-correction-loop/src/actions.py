def corrective_action(action_id,action_type,target_layer,
                      target_ref=None,parameters=None,reason=None):
    return {"action_id":action_id,"action_type":action_type,
            "target_layer":target_layer,"target_ref":target_ref,
            "parameters":parameters or {},"reason":reason}

def action_types():
    return ["RETRIEVE","TRANSFORM","CHANGE_REPRESENTATION",
            "UPDATE_CONTRACT","CHANGE_BACKEND","REGENERATE",
            "REVIEW","RETRY","ROLLBACK","NO_ACTION"]
