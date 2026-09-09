def neighbors(graph,node_id,relation=None,direction="out"):
    out=[]
    for e in graph.get("edges",[]):
        if direction=="out" and e["source"]==node_id:
            if relation is None or e["relation"]==relation: out.append(e)
        elif direction=="in" and e["target"]==node_id:
            if relation is None or e["relation"]==relation: out.append(e)
    return out

def prerequisites(graph,node_id):
    return neighbors(graph,node_id,"requires","in")+neighbors(graph,node_id,"depends_on","in")

def higher_knowledge(graph,node_id):
    return [e for e in graph.get("external_nodes",[]) if node_id in e.get("derived_from",[])]
