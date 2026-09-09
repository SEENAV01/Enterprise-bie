def action_constraint(constraint_id,action_type,
                     kind,value,priority="required"):
    return {"constraint_id":constraint_id,"action_type":action_type,
            "kind":kind,"value":value,"priority":priority}

def satisfies_constraints(action,constraints):
    errors=[]
    for c in constraints:
        if c.get("priority")!="required": continue
        if c.get("action_type") and c["action_type"]!=action.get("action_type"):
            continue
        if c.get("kind")=="FORBID":
            errors.append("FORBIDDEN_ACTION")
    return errors
