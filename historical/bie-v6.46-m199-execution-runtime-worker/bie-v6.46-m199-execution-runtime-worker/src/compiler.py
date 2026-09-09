from worker import worker,ready
from runtime import runtime,available as runtime_available
from job import job,queued
from task import task,runnable
from attempt import attempt,running
from placement import placement,selected
from cancellation import cancellation,requested
from heartbeat import heartbeat,healthy as heartbeat_healthy
from health import worker_health,available as worker_available
from audit import execution_event,successful
from observability import execution_metric,healthy

def compile_execution():
    w=worker("worker-1","runtime-1",["python","gpu"])
    rt=runtime("runtime-1","container","1.0",{"os":"linux"})
    jb=job("job-1",{"image":"bie/worker"},10,
           "2026-09-01T12:00:00Z")
    t=task("task-1","job-1",{"action":"compile"})
    at=attempt("attempt-1","task-1",1,"worker-1")
    pl=placement("task-1","worker-1",{"region":"primary"},0.98)
    ca=cancellation("task-2","USER_REQUEST","user-1")
    hb=heartbeat("worker-1","2026-09-01T10:00:00Z",
                 {"cpu":0.25},17)
    ht=worker_health("worker-1","HEALTHY",3,
                     "2026-09-01T10:00:00Z")
    ev=execution_event("ee-1","job-1","EXECUTE","SUCCESS","worker-1")
    met=execution_metric("em-1","job-1","EXECUTE","SUCCESS",20,80,1)
    return {"schema_version":"6.46","worker":w,"runtime":rt,
            "job":jb,"task":t,"attempt":at,"placement":pl,
            "cancellation":ca,"heartbeat":hb,"health":ht,
            "audit":ev,"observability":met,
            "quality_gate":{"valid":True,"errors":[]},
            "checks":{
              "worker_ready":ready(w),
              "runtime_available":runtime_available(rt),
              "job_queued":queued(jb),
              "task_runnable":runnable(t),
              "attempt_running":running(at),
              "placement_selected":selected(pl),
              "cancellation_requested":requested(ca),
              "heartbeat_healthy":heartbeat_healthy(hb),
              "worker_available":worker_available(ht),
              "audit_success":successful(ev),
              "observability_healthy":healthy(met)
            }}
