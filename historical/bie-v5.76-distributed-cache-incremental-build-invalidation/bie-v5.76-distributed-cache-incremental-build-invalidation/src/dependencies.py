def dependency_graph(nodes):
    return {n["node_id"]:set(n.get("depends_on",[])) for n in nodes}

def reverse_dependencies(nodes):
    graph=dependency_graph(nodes)
    reverse={k:set() for k in graph}
    for node,deps in graph.items():
        for dep in deps:
            reverse.setdefault(dep,set()).add(node)
    return reverse
