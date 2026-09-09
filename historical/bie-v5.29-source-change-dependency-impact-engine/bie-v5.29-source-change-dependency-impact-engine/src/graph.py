def dependency_graph(nodes,edges):
    parents={n:[] for n in nodes}; children={n:[] for n in nodes}
    for a,b in edges:
        if a in children and b in parents:
            children[a].append(b); parents[b].append(a)
    return {"nodes":nodes,"edges":edges,"parents":parents,"children":children}

def downstream(graph,start):
    seen=set(); queue=list(start)
    while queue:
        n=queue.pop(0)
        for child in graph["children"].get(n,[]):
            if child not in seen:
                seen.add(child); queue.append(child)
    return list(seen)
