def timing_constraint(constraint_id,target,kind,value=None,
                       min_value=None,max_value=None,priority="preferred"):
    return {"constraint_id":constraint_id,"target":target,"kind":kind,
            "value":value,"min_value":min_value,"max_value":max_value,
            "priority":priority}

def timing_hint(target,kind,value=None,reason=None):
    return {"target":target,"kind":kind,"value":value,"reason":reason}
