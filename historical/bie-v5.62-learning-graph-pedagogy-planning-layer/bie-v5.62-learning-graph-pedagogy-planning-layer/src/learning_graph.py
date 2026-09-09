def learning_graph(nodes=None,relations=None):
    return {"nodes":nodes or [],"relations":relations or []}

def prerequisites(graph,concept_id):
    return [r["source"] for r in graph.get("relations",[])
            if r["target"]==concept_id and
            r["relation_type"]=="PREREQUISITE_OF"]

def dependents(graph,concept_id):
    return [r["target"] for r in graph.get("relations",[])
            if r["source"]==concept_id and
            r["relation_type"]=="PREREQUISITE_OF"]
