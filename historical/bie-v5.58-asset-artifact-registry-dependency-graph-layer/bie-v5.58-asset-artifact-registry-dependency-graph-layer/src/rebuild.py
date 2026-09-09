def rebuild_plan(graph,changed_refs,registry=None):
    invalidated=set()
    pending=list(changed_refs)
    while pending:
        ref=pending.pop(0)
        if ref in invalidated: continue
        invalidated.add(ref)
        for e in graph.get("edges",[]):
            if e["source"]==ref and e["relation"]=="DEPENDS_ON":
                pending.append(e["target"])
    return {"changed":sorted(changed_refs),
            "invalidated":sorted(invalidated),
            "rebuild_order":topological_rebuild_order(
                graph,invalidated)}

def topological_rebuild_order(graph,refs):
    refs=set(refs)
    remaining=set(refs)
    order=[]
    while remaining:
        ready=[]
        for r in remaining:
            deps=[e["source"] for e in graph.get("edges",[])
                  if e["target"]==r and e["relation"]=="DEPENDS_ON"]
            if not any(d in remaining for d in deps):
                ready.append(r)
        if not ready:
            raise ValueError("DEPENDENCY_CYCLE")
        for r in sorted(ready):
            order.append(r); remaining.remove(r)
    return order
