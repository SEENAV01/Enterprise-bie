from graph import graph, add_node, add_edge

def build_knowledge_graph(concepts, relationships):
    g=graph("kg-1","KNOWLEDGE","6.51")
    for c in concepts:
        add_node(g,c["concept_id"],"CONCEPT",c["label"],c.get("evidence_ids",[]))
    for r in relationships:
        add_edge(g,r["rel_id"],r["source"],r["target"],
                 r["relation"],r.get("evidence_ids",[]))
    return g

def grounded(g):
    return all(n["evidence_ids"] for n in g["nodes"])
