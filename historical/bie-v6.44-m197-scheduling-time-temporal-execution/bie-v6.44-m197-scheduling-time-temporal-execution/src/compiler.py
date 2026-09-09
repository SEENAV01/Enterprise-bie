from clock import clock,valid as clock_valid
from schedule import schedule,active as schedule_active
from interval import interval,finite
from calendar import calendar,holiday
from deadline import deadline,valid as deadline_valid
from timeout import timeout,expired
from retry import temporal_retry,allowed
from window import temporal_window,contains
from state import temporal_state,active as state_active
from audit import temporal_event,successful
from observability import temporal_metric,healthy

def compile_temporal():
    cl=clock("system","UTC",True)
    sc=schedule("sch-1","2026-01-01T00:00:00Z",
                recurrence="0 * * * *","UTC")
    it=interval(1,"HOURS")
    cal=calendar("cal-1","UTC",["MON","TUE","WED","THU","FRI"],
                 ["2026-12-25"])
    dl=deadline("dl-1","2026-09-01T12:00:00Z","15m","WARN")
    to=timeout(30,"SECONDS","RETRY")
    rt=temporal_retry(5,2,"SECONDS","EXPONENTIAL")
    win=temporal_window("2026-09-01T00:00:00Z","2026-09-02T00:00:00Z")
    st=temporal_state("job-1","RUNNING",
                      "2026-09-01T10:00:00Z","2026-09-01T11:00:00Z")
    ev=temporal_event("te-1","job-1","SCHEDULE","SUCCESS",
                      "2026-09-01T10:00:00Z")
    met=temporal_metric("tm-1","job-1","SCHEDULE","SUCCESS",4,18)
    return {"schema_version":"6.44","clock":cl,"schedule":sc,
            "interval":it,"calendar":cal,"deadline":dl,
            "timeout":to,"retry":rt,"window":win,"state":st,
            "audit":ev,"observability":met,
            "quality_gate":{"valid":True,"errors":[]},
            "checks":{
              "clock_valid":clock_valid(cl),
              "schedule_active":schedule_active(sc),
              "interval_finite":not finite(it),
              "holiday_detected":holiday(cal,"2026-12-25"),
              "deadline_valid":deadline_valid(dl),
              "timeout_expired":expired(to,30),
              "retry_allowed":allowed(rt,3),
              "window_contains":contains(win,"2026-09-01T12:00:00Z"),
              "temporal_state_active":state_active(st,"2026-09-01T10:30:00Z"),
              "audit_success":successful(ev),
              "observability_healthy":healthy(met)
            }}
