def validate_diagram(graph):
    ids={n["id"] for n in graph.get("nodes",[])}
    errors=[]
    for edge in graph.get("edges",[]):
        if edge["source"] not in ids or edge["target"] not in ids:
            errors.append("DIAGRAM_EDGE_REFERENCE")
    for n in graph.get("nodes",[]):
        if not n.get("label"): errors.append(f"DIAGRAM_LABEL_MISSING:{n['id']}")
    return {"valid":not errors,"errors":errors}
