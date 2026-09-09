from learning_graph import prerequisites

def prerequisite_closure(graph,target_ids):
    seen=set()
    stack=list(target_ids)
    while stack:
        x=stack.pop()
        if x in seen: continue
        seen.add(x)
        stack.extend(prerequisites(graph,x))
    return sorted(seen)

def topological_learning_order(graph,target_ids):
    nodes=set(prerequisite_closure(graph,target_ids))
    order=[]
    while nodes:
        ready=[]
        for n in nodes:
            deps=[r["source"] for r in graph.get("relations",[])
                  if r["target"]==n and
                  r["relation_type"]=="PREREQUISITE_OF"]
            if not any(d in nodes for d in deps):
                ready.append(n)
        if not ready: raise ValueError("LEARNING_GRAPH_CYCLE")
        for n in sorted(ready):
            order.append(n); nodes.remove(n)
    return order
