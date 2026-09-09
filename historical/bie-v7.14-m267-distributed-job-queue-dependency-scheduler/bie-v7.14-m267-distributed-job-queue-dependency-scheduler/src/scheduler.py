from dag import ready_nodes
from queue import enqueue
from critical_path import critical_path

def build_ready_queue(nodes,edges,completed,job_specs):
    ready=set(ready_nodes(nodes,edges,completed))
    q=[]
    for spec in job_specs:
        if spec["job_id"] in ready:
            enqueue(q,spec,spec.get("priority",50))
    return q

def schedule(nodes,edges,completed,job_specs,durations):
    q=build_ready_queue(nodes,edges,completed,job_specs)
    cp=critical_path(nodes,edges,durations)
    return {"ready_queue":q,"critical_path":cp}
