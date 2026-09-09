def create_scene_graph(scene_id, nodes=None, edges=None):
    return {"scene_id":scene_id,"nodes":nodes or [],"edges":edges or []}

def add_node(graph,node):
    graph["nodes"].append(node); return graph

def add_edge(graph,source,target,relation="DEPENDS_ON"):
    graph["edges"].append({"source":source,"target":target,"relation":relation}); return graph

def validate_graph(graph):
    ids=[n.get("id") for n in graph["nodes"]]
    known=set(ids); errors=[]
    if len(ids)!=len(known): errors.append("DUPLICATE_NODE_ID")
    for e in graph["edges"]:
        if e["source"] not in known or e["target"] not in known: errors.append("UNKNOWN_EDGE_NODE")
    return {"valid":not errors,"errors":errors}
