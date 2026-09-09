COMPONENT_TYPES=["TEXT","EQUATION","IMAGE","SVG","SHAPE","GRAPH","VECTOR_FIELD",
"PARTICLE_SYSTEM","GROUP","CAPTION","AUDIO"]

def component_spec(component_id,component_type,props=None):
    if component_type not in COMPONENT_TYPES: raise ValueError("UNKNOWN_COMPONENT_TYPE")
    return {"component_id":component_id,"type":component_type,"props":props or {}}
