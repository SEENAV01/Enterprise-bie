def term(field,value):
    return {"type":"TERM","field":field,"value":value}

def boolean(operator,clauses):
    if operator not in {"AND","OR","NOT"}:
        raise ValueError("INVALID_BOOLEAN_OPERATOR")
    return {"type":"BOOLEAN","operator":operator,
            "clauses":clauses}

def query(clauses):
    return {"type":"QUERY","clauses":clauses}
