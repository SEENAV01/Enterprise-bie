def template(template_id,name,template_type,
             component_refs=None,layout_ref=None):
    return {"template_id":template_id,"name":name,
            "template_type":template_type,
            "component_refs":component_refs or [],
            "layout_ref":layout_ref}

def template_types():
    return ["TITLE","DEFINITION","COMPARISON","PROCESS",
            "DIAGRAM","EQUATION","TIMELINE","CHART","QUIZ",
            "SIMULATION","SUMMARY"]
