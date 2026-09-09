def primitive(primitive_id,primitive_type,props=None,semantic_role=None):
    return {"primitive_id":primitive_id,"primitive_type":primitive_type,
            "props":props or {},"semantic_role":semantic_role}

def primitive_types():
    return ["POINT","LINE","ARROW","VECTOR","AXIS","SHAPE","TEXT",
            "LABEL","GRID","CHART","EQUATION","IMAGE","PARTICLE",
            "PATH","GROUP"]
