def dependency_edge(source,target,relation="DEPENDS_ON",
                    reason=None):
    return {"source":source,"target":target,
            "relation":relation,"reason":reason}

def dependency_graph(nodes=None,edges=None):
    return {"nodes":nodes or [],"edges":edges or []}

def downstream(graph,changed):
    targets=[]
    for e in graph.get("edges",[]):
        if e["source"] in changed and e["relation"]=="DEPENDS_ON":
            targets.append(e["target"])
    return sorted(set(targets))

def upstream(graph,target):
    return sorted(set(e["source"] for e in graph.get("edges",[])
                       if e["target"]==target))
