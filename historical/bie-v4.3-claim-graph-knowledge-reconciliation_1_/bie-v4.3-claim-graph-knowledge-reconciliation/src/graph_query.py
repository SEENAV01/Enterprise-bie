def neighbors(graph,node_id,edge_type=None):
    ids=[]
    for e in graph.get("edges",[]):
        if e["source"]==node_id and (edge_type is None or e["type"]==edge_type):
            ids.append(e["target"])
        elif e["target"]==node_id and (edge_type is None or e["type"]==edge_type):
            ids.append(e["source"])
    return ids

def claims_for_concept(graph, concept_id):
    related=neighbors(graph,concept_id)
    return [n for n in graph["nodes"] if n["id"] in related and n["type"]=="CLAIM"]
