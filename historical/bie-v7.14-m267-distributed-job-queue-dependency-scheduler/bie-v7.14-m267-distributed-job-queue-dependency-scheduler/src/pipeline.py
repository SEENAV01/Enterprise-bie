from dag import validate_dag,ready_nodes
from scheduler import schedule
from retry import mark_failure
from idempotency import execution_key,accept_once
from critical_path import concurrency_limit

def build_m267_runtime():
    nodes=[{"id":"scene"},{"id":"audio"},{"id":"render"}]
    edges=[{"source":"scene","target":"render"},{"source":"audio","target":"render"}]
    dag=validate_dag(nodes,edges)
    completed={"scene","audio"}
    specs=[{"job_id":"render","priority":100}]
    scheduled=schedule(nodes,edges,completed,specs,{"scene":3,"audio":2,"render":4})
    job={"job_id":"render","attempt":0}
    failed=mark_failure(job,"RENDER_TIMEOUT",3)
    store={}
    key=execution_key("render",0)
    first=accept_once(store,key,{"uri":"render.mp4"})
    duplicate=accept_once(store,key,{"uri":"other.mp4"})
    return {"schema_version":"7.14","dag":dag,"ready":ready_nodes(nodes,edges,completed),
            "schedule":scheduled,"failed_job":failed,
            "idempotency":{"first":first,"duplicate":duplicate},
            "concurrency":{"allowed":concurrency_limit(5,4,1)},
            "queue_gate":{"valid":dag["valid"] and bool(scheduled["ready_queue"]) and
                          not duplicate["accepted"],"errors":[]}}
