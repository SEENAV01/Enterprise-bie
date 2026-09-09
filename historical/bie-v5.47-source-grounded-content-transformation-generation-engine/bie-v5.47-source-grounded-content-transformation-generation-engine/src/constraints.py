def transformation_constraint(constraint_id,kind,value,
                              severity="required"):
    return {"constraint_id":constraint_id,"kind":kind,
            "value":value,"severity":severity}

def validate_output(output,constraints):
    errors=[]
    for c in constraints:
        if c.get("severity")!="required": continue
        if c.get("kind")=="REQUIRE_SOURCE_CITATION" and not output.get("source_refs"):
            errors.append("SOURCE_CITATION_REQUIRED")
        if c.get("kind")=="FORBID_UNGROUNDED_ADDITIONS" and output.get("generated_refs"):
            errors.append("UNGROUNDED_ADDITION_FORBIDDEN")
    return sorted(set(errors))
