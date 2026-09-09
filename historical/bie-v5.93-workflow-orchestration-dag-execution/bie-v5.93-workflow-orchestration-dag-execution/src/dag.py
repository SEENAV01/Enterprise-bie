def dag(workflow_id,nodes=None,edges=None):
    return {"workflow_id":workflow_id,
            "nodes":nodes or [],"edges":edges or []}

def dependencies(graph,node_id):
    return [e["from"] for e in graph.get("edges",[])
            if e["to"]==node_id]

def ready_nodes(graph,completed):
    done=set(completed)
    return [n for n in graph.get("nodes",[])
            if n not in done and all(x in done for x in dependencies(graph,n))]
