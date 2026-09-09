from dependencies import reverse_dependencies

def affected_nodes(nodes,changed):
    reverse=reverse_dependencies(nodes)
    affected=set(changed)
    stack=list(changed)
    while stack:
        current=stack.pop()
        for child in reverse.get(current,set()):
            if child not in affected:
                affected.add(child)
                stack.append(child)
    return affected

def invalidation_plan(nodes,changed):
    affected=affected_nodes(nodes,changed)
    return {"changed":list(changed),
            "invalidated":sorted(affected)}
