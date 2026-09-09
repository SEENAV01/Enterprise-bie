def style_drift(instance_style,canonical_style):
    mismatches={}
    for k,v in canonical_style.items():
        if instance_style.get(k)!=v:
            mismatches[k]={"expected":v,"actual":instance_style.get(k)}
    return {"drift":bool(mismatches),"mismatches":mismatches}

def component_drift(instance,component):
    return {"drift":instance.get("component_id")!=component.get("component_id")}
