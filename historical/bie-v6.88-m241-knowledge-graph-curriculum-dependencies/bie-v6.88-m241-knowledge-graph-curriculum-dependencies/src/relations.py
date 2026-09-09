RELATIONS={"PREREQUISITE","RELATED","PART_OF","EXAMPLE_OF","DEPENDS_ON"}

def validate_relations(edges):
    errors=[]
    for e in edges:
        if e.get("relation") not in RELATIONS:
            errors.append({"edge":e,"error":"UNKNOWN_RELATION"})
        if e.get("source")==e.get("target") and e.get("relation")=="PREREQUISITE":
            errors.append({"edge":e,"error":"SELF_PREREQUISITE"})
    return {"passed":not errors,"errors":errors}
