def add_lineage(graph, child, parents):
    graph[child]=list(dict.fromkeys(parents))
    return graph

def ancestors(graph,node):
    seen=set()
    stack=list(graph.get(node,[]))
    while stack:
        x=stack.pop()
        if x in seen: continue
        seen.add(x); stack.extend(graph.get(x,[]))
    return sorted(seen)
