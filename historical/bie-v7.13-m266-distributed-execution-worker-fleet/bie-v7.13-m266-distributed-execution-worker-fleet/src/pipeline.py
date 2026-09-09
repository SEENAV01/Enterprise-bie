from workers import register_worker,heartbeat,mark_unhealthy
from scheduler import match_worker,dispatch
from leases import acquire_lease,expire_lease
from faults import recover_expired_job,isolate_worker
from autoscale import desired_workers,scaling_action

def build_m266_runtime():
    workers=[
      register_worker("w-render-1",["render","qa"],2),
      register_worker("w-media-1",["tts","image"],2),
      register_worker("w-render-2",["render"],1)
    ]
    heartbeat(workers[0],100)
    job={"job_id":"scene-001-render","capability":"render","status":"QUEUED","attempt":0}
    worker=match_worker(workers,"render")
    dispatch_result=dispatch(job,worker)
    lease=acquire_lease(job["job_id"],worker["worker_id"],"lease-001",160)
    expired=expire_lease(lease)
    recovery=recover_expired_job(job,expired)
    failed=mark_unhealthy(workers[0])
    isolated=isolate_worker(failed)
    desired=desired_workers(8,2)
    scale=scaling_action(len(workers),desired)
    return {"schema_version":"7.13","workers":workers,"dispatch":dispatch_result,
            "lease":expired,"recovery":recovery,"isolated_worker":isolated,
            "autoscaling":{"queue_depth":8,"desired_workers":desired,
                           "current_workers":len(workers),"action":scale},
            "distributed_execution_gate":{
                "valid":dispatch_result["status"]=="DISPATCHED" and
                        recovery["requeue"] and isolated["status"]=="ISOLATED",
                "errors":[]}}
