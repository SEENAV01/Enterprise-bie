def create_graph():
    return {"entities":{},"relations":[]}

def add_entity(graph, entity):
    graph["entities"][entity["entity_id"]]=entity
    return entity

def neighbors(graph, entity_id, predicate=None):
    out=[]
    for r in graph["relations"]:
        if r["source"]==entity_id or r["target"]==entity_id:
            if predicate is None or r["predicate"]==predicate: out.append(r)
    return out
