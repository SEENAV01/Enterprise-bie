def capability_match(contract,backend):
    required=contract.get("representation_type")
    caps=set(backend.get("capabilities",[]))
    mapping={
      "DIAGRAM":"2D_VECTOR","ANIMATION":"2D_ANIMATION",
      "VIDEO":"VIDEO","AUDIO":"AUDIO","SIMULATION":"SIMULATION",
      "INTERACTIVE":"INTERACTIVE","TEXT":"TEXT","DOCUMENT":"DOCUMENT"
    }
    needed=mapping.get(required,required)
    return needed in caps

def constraint_match(contract,backend):
    constraints=contract.get("constraints",{})
    profile=backend.get("resource_profile",{})
    for key,value in constraints.get("resource",{}).items():
        if key in profile and profile[key] < value:
            return False
    return True
