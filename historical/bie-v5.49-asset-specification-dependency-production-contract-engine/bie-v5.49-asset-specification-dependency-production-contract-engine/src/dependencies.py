def dependency(source_id,target_id,kind="REQUIRES",
               optional=False,reason=None):
    return {"source_id":source_id,"target_id":target_id,
            "kind":kind,"optional":optional,"reason":reason}

def dependency_graph(nodes,edges):
    return {"nodes":nodes,"edges":edges}

def validate_dependencies(nodes,edges):
    ids={n for n in nodes}
    errors=[]
    for e in edges:
        if e.get("source_id") not in ids or e.get("target_id") not in ids:
            errors.append("DEPENDENCY_NODE_MISSING")
    return sorted(set(errors))
