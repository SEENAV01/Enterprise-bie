def effect_key(saga_id, step_id):
    return f"{saga_id}:{step_id}"

def apply_once(effect_store,key,effect):
    if key in effect_store:
        return {"applied":False,"duplicate":True,"effect":effect_store[key]}
    effect_store[key]=effect
    return {"applied":True,"duplicate":False,"effect":effect}

def exactly_once_effect_contract(result):
    return bool(result["applied"]) ^ bool(result["duplicate"])
