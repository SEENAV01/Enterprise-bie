def backward_compatible(old_schema,new_schema):
    old_req=set(old_schema.get("required",[]))
    new_req=set(new_schema.get("required",[]))
    # Adding a new required field can break old producers/consumers.
    return new_req.issubset(old_req)

def forward_compatible(old_schema,new_schema):
    old_req=set(old_schema.get("required",[]))
    new_req=set(new_schema.get("required",[]))
    # Removing a required field can break consumers expecting it.
    return old_req.issubset(new_req)

def compatibility(old_schema,new_schema):
    return {
      "backward":backward_compatible(old_schema,new_schema),
      "forward":forward_compatible(old_schema,new_schema)
    }
