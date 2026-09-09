def adaptive_hook(hook_id,trigger,action,target=None):
    return {"hook_id":hook_id,"trigger":trigger,
            "action":action,"target":target}

def hook_types():
    return ["ON_MASTERY","ON_FAILURE","ON_MISCONCEPTION",
            "ON_REQUEST_REPEAT","ON_FAST_PROGRESS"]
