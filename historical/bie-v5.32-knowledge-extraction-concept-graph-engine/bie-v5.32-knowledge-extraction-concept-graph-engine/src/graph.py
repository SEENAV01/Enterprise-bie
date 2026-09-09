def concept_graph(concepts=None,entities=None,
                  relationships=None,equations=None,examples=None):
    return {"concepts":concepts or [],"entities":entities or [],
            "relationships":relationships or [],
            "equations":equations or [],"examples":examples or []}

def neighbors(graph,node_id,relation_type=None):
    out=[]
    for r in graph.get("relationships",[]):
        if r.get("source")==node_id or r.get("target")==node_id:
            if relation_type is None or r.get("relation_type")==relation_type:
                out.append(r)
    return out
