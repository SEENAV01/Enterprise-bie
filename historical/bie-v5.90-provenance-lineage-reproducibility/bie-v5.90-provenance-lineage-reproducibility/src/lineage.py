def lineage_edge(parent,child,relation="DERIVED_FROM"):
    return {"parent":parent,"child":child,"relation":relation}

def lineage_graph(edges):
    return {"edges":edges}

def ancestors(graph,node):
    found=set(); changed=True
    while changed:
        changed=False
        for e in graph.get("edges",[]):
            if e["child"] in (found|{node}) and e["parent"] not in found:
                found.add(e["parent"]); changed=True
    return sorted(found)
