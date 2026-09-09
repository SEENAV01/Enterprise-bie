from dag import topological_ready

def schedule_batches(nodes,max_parallel=4):
    working=[dict(n) for n in nodes]
    batches=[]
    while True:
        ready=topological_ready(working)
        if not ready: break
        batch=ready[:max_parallel]
        batches.append([n["node_id"] for n in batch])
        for n in working:
            if n["node_id"] in {x["node_id"] for x in batch}:
                n["status"]="COMPLETE"
    return batches
