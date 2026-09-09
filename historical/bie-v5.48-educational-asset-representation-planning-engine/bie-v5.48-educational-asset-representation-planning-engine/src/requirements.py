def requirement(requirement_id,kind,value,severity="required"):
    return {"requirement_id":requirement_id,"kind":kind,
            "value":value,"severity":severity}

def validate_representation(spec,requirements):
    errors=[]
    for r in requirements:
        if r.get("severity")!="required": continue
        if r.get("kind")=="REQUIRE_INTERACTION" and            spec.get("representation_type") not in ["INTERACTIVE","SIMULATION"]:
            errors.append("INTERACTION_REQUIRED")
        if r.get("kind")=="REQUIRE_VISUAL" and            spec.get("representation_type") not in ["DIAGRAM","ANIMATION",
                                                    "SIMULATION","CHART"]:
            errors.append("VISUAL_REQUIRED")
    return sorted(set(errors))
