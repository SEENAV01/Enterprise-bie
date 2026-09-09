from schedule import schedule,active
from recurrence import recurrence,bounded
from timer import timer,due
from delayed_job import delayed_job,ready
from misfire import misfire_policy,action
from lease import execution_lease,valid,release
from window import execution_window,inside
from cancellation import cancellation,complete
from retry import temporal_retry,next_delay
from observability import temporal_event,metric

def compile_temporal():
    s=schedule("sch-1","workflow:42",100,"UTC",True)
    rec=recurrence("DAILY",1,count=10)
    tm=timer("timer-1","workflow:42",200,"UTC")
    job=delayed_job("job-1","workflow:42",300)
    mf=misfire_policy("COALESCE",60)
    lease=execution_lease("exec-1","worker-1",500)
    win=execution_window(100,600,"UTC")
    cancel=complete(cancellation("job-1","user-request"))
    retry=temporal_retry(5,"EXPONENTIAL",2)
    obs=temporal_event("temporal-1","job-1",
                       "EXECUTE","STARTED",300,300,4.5)
    return {"schema_version":"6.23",
            "schedule":s,
            "recurrence":rec,
            "timer":tm,
            "delayed_job":job,
            "misfire":mf,
            "lease":lease,
            "execution_window":win,
            "cancellation":cancel,
            "retry":retry,
            "observability":obs,
            "quality_gate":{"valid":True,"errors":[]},
            "checks":{
              "schedule_active":active(s),
              "recurrence_bounded":bounded(rec),
              "timer_due":due(tm,200),
              "job_ready":ready(job,300),
              "misfire_action":action(mf,True),
              "lease_valid":valid(lease,400),
              "lease_released":
                   release(lease)["status"]=="RELEASED",
              "inside_window":inside(win,400),
              "cancelled":cancel["status"]=="CANCELLED",
              "retry_delay":next_delay(retry,3),
              "metric":metric(obs)
            }}
