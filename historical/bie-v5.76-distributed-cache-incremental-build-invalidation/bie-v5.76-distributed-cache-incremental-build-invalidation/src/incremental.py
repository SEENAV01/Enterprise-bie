def reusable(node_id,invalidated,cache_hit):
    return cache_hit and node_id not in set(invalidated)

def build_plan(nodes,invalidated,cache):
    plan=[]
    for n in nodes:
        nid=n["node_id"]
        if nid in set(invalidated):
            plan.append({"node_id":nid,"action":"REBUILD"})
        elif cache.get(nid):
            plan.append({"node_id":nid,"action":"REUSE"})
        else:
            plan.append({"node_id":nid,"action":"BUILD"})
    return plan
