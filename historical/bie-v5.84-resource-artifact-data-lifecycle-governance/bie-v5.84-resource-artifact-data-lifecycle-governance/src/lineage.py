def lineage_edge(parent_id,child_id,relation="DERIVED_FROM"):
    return {"parent_id":parent_id,"child_id":child_id,
            "relation":relation}

def dependency_graph(edges):
    graph={}
    for e in edges:
        graph.setdefault(e["parent_id"],set()).add(e["child_id"])
    return graph
