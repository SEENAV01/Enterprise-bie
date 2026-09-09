def component_ref(component_id,name,props=None):
    return {"component_id":component_id,"name":name,"props":props or {}}

def component_graph(components):
    return {"components":components}
