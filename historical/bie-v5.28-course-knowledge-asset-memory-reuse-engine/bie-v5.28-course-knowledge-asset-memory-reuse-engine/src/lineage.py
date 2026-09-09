def lineage_node(node_id,parents=None,children=None):
    return {"node_id":node_id,"parents":parents or [],
            "children":children or []}

def lineage_graph(nodes):
    return {"nodes":nodes}
