from traversal import traverse

def graph_retrieve(graph, entity_id, predicate=None, max_hops=2):
    result=traverse(graph,entity_id,max_hops,predicate)
    return {"entity_id":entity_id,"nodes":result["nodes"],"paths":result["paths"]}

def relation_evidence(result):
    return [p["relation"] for p in result["paths"] if p["relation"].get("provenance")]
