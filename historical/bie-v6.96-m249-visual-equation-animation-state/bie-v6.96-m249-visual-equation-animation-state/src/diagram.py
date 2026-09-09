def create_diagram(diagram_id, elements=None, relations=None):
    return {"diagram_id":diagram_id,"elements":elements or [],"relations":relations or []}

def update_element(diagram, element_id, **changes):
    for e in diagram["elements"]:
        if e.get("id")==element_id:
            e.update(changes); return diagram
    raise KeyError(element_id)

def validate_diagram(diagram):
    ids=[e.get("id") for e in diagram.get("elements",[])]
    errors=["DUPLICATE_ELEMENT_ID"] if len(ids)!=len(set(ids)) else []
    return {"passed":not errors,"errors":errors}
