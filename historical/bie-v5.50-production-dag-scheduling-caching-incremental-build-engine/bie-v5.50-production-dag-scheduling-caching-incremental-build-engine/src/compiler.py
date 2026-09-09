from dag import topological_ready
from invalidation import invalidate_nodes

def compile_build(nodes,changed_ids=None,max_parallel=4):
    nodes=[dict(n) for n in nodes]
    if changed_ids:
        invalid=invalidate_nodes(changed_ids,nodes)
        for n in nodes:
            if n["node_id"] in invalid:
                n["status"]="PENDING"
    batches=[]
    while True:
        ready=topological_ready(nodes)
        if not ready: break
        batch=ready[:max_parallel]
        batches.append([n["node_id"] for n in batch])
        for n in nodes:
            if n["node_id"] in {x["node_id"] for x in batch}:
                n["status"]="COMPLETE"
    unresolved=[n["node_id"] for n in nodes
                if n.get("status")!="COMPLETE"]
    return {"schema_version":"5.50","batches":batches,
            "nodes":nodes,"invalidated":
              invalidate_nodes(changed_ids or [],nodes),
            "quality_gate":{"valid":not unresolved,
                            "errors":([] if not unresolved else
                                     ["UNRESOLVED_BUILD_NODES"])}}
