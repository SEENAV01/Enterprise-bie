def component(component_id,component_type,
               props=None,semantic_refs=None,
               children=None):
    return {"component_id":component_id,
            "component_type":component_type,
            "props":props or {},
            "semantic_refs":semantic_refs or [],
            "children":children or []}

def validate_component(component):
    required=["component_id","component_type"]
    return all(component.get(k) for k in required)
