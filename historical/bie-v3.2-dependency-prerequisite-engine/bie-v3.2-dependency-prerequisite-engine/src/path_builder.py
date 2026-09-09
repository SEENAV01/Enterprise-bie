def adjacency(dependencies):
    g={}
    for d in dependencies:
        g.setdefault(d["source"],[]).append(d)
    return g

def learning_path(start, dependencies, max_nodes=100):
    g=adjacency(dependencies)
    path=[]; seen=set()
    stack=[start]
    while stack and len(path)<max_nodes:
        x=stack.pop(0)
        if x in seen: continue
        seen.add(x); path.append(x)
        for d in g.get(x,[]):
            stack.append(d["target"])
    return path
