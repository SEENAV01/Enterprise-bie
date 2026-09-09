from graph import graph, add_node, add_edge

def build_learning_graph(learning_nodes, dependency_edges):
    g=graph("lg-1","LEARNING","6.51")
    for n in learning_nodes:
        add_node(g,n["id"],n["type"],n["label"],
                 n.get("evidence_ids",[]),n.get("metadata",{}))
    for e in dependency_edges:
        add_edge(g,e["edge_id"],e["source"],e["target"],
                 e["relation"],e.get("evidence_ids",[]))
    return g

def valid_order(g):
    return bool(g["nodes"]) and all(e["source"] and e["target"] for e in g["edges"])
