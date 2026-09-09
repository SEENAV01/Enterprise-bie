def transition(state,operation_id,
               operation,new_state):
    applied=set(state.get("_operations",[]))
    if operation_id in applied:
        return {"status":"ALREADY_APPLIED",
                "state":state}
    out=dict(new_state)
    out["_operations"]=list(applied|{operation_id})
    return {"status":"APPLIED",
            "operation":operation,
            "state":out}
