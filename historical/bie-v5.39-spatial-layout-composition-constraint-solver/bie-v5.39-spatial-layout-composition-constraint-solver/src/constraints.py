def constraint(constraint_id,constraint_type,targets,
              value=None,priority="required"):
    return {"constraint_id":constraint_id,"constraint_type":constraint_type,
            "targets":targets,"value":value,"priority":priority}

def constraint_types():
    return ["ALIGN_LEFT","ALIGN_RIGHT","ALIGN_TOP","ALIGN_BOTTOM",
            "CENTER_X","CENTER_Y","STACK_VERTICAL","STACK_HORIZONTAL",
            "CONTAIN","KEEP_GAP","AVOID_OVERLAP","ANCHOR","STAY_IN_SAFE_AREA",
            "FOLLOW","FOCUS"]
