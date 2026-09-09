def graph(graph_id, graph_type, version="1.0"):
    if graph_type not in {"KNOWLEDGE","LEARNING"}:
        raise ValueError("INVALID_GRAPH_TYPE")
    return {"graph_id":graph_id,"graph_type":graph_type,"version":version,
            "nodes":[],"edges":[]}

def add_node(g, node_id, node_type, label, evidence_ids=None, metadata=None):
    g["nodes"].append({"node_id":node_id,"node_type":node_type,"label":label,
                       "evidence_ids":evidence_ids or [],
                       "metadata":metadata or {}})
    return g

def add_edge(g, edge_id, source, target, relation, evidence_ids=None):
    g["edges"].append({"edge_id":edge_id,"source":source,"target":target,
                       "relation":relation,"evidence_ids":evidence_ids or []})
    return g
