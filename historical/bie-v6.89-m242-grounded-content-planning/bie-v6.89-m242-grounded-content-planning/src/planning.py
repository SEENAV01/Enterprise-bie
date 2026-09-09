def plan_concept(concept_id, prerequisites=None, objectives=None):
    return {"concept_id":concept_id,"prerequisites":prerequisites or [],
            "objectives":objectives or []}

def build_content_plan(graph, target_concepts):
    nodes={n["node_id"]:n for n in graph.get("nodes",[])}
    edges=graph.get("edges",[])
    req={x:[] for x in target_concepts}
    for e in edges:
        if e.get("relation")=="PREREQUISITE" and e["target"] in req:
            req[e["target"]].append(e["source"])
    return [plan_concept(cid,req.get(cid,[]),[nodes[cid]["label"]] if cid in nodes else [])
            for cid in target_concepts]
