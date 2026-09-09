def ready_nodes(dag, completed):
    completed=set(completed)
    incoming={n["id"]:set() for n in dag["nodes"]}
    for e in dag["edges"]: incoming[e["target"]].add(e["source"])
    return sorted([i for i,d in incoming.items() if i not in completed and d.issubset(completed)])

def schedule_course(dag, completed, capacity):
    ready=ready_nodes(dag,completed)
    return {"selected":ready[:capacity],"remaining":ready[capacity:]}
