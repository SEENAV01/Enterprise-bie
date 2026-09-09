from job import job
from queue import JobQueue
from resources import resource_pool,allocate
from worker import worker,can_run
from attempt import attempt
from retry import retry_policy,should_retry
from checkpoint import checkpoint
from failure import worker_failure,recovery_action
from aggregation import aggregate

def demo_runtime():
    q=JobQueue()
    j=job("job-1","lesson-2",resources={"cpu":2,"memory":4},
          payload={"stage":"RENDERED"})
    q.enqueue(j)

    pool=resource_pool(8,32,1)
    w=worker("worker-1",["cpu","gpu"])
    picked=q.dequeue()
    remaining=allocate(picked["resources"],pool)

    a1=attempt("attempt-1",picked["job_id"],w["worker_id"],1,"FAILED",
               error="WORKER_LOST")
    policy=retry_policy(3)
    retry=should_retry(picked,a1["error"],policy)

    cp=checkpoint("cp-1",picked["job_id"],1,"COMPOSED",
                  ["artifact://composition"],{"frame":1200})
    failure=worker_failure(w["worker_id"],"PROCESS_CRASH",
                           [picked["job_id"]],True)

    result={"job_id":picked["job_id"],
            "status":"SUCCEEDED" if retry else "FAILED",
            "attempts":2,"checkpoint_ref":cp["checkpoint_id"]}
    agg=aggregate([result])

    return {
        "schema_version":"6.63",
        "queue":{"remaining":len(q)},
        "job":picked,
        "resource_pool":pool,
        "resources_after_allocation":remaining,
        "worker":w,
        "attempts":[a1],
        "retry_policy":policy,
        "retry_triggered":retry,
        "checkpoint":cp,
        "worker_failure":failure,
        "recovery_action":recovery_action(failure),
        "aggregation":agg,
        "runtime_gate":{"valid":(
            picked["job_id"]=="job-1"
            and retry
            and cp["checkpoint_id"]
            and recovery_action(failure)=="REQUEUE_AFFECTED_JOBS"
            and agg["status"]=="SUCCEEDED"
        ),"errors":[]}
    }
