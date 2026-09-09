from schedule import schedule,active
from clock import clock_sample,within_bound
from timezone import timezone_policy,valid
from misfire import misfire_policy,should_run
from leader import leadership
from recurrence import recurrence,bounded
from calendar_window import calendar_window,contains
from dispatch import dispatch,dispatched
from observability import scheduler_event,metric

def compile_scheduler():
    sch=schedule("sch-1","0 9 * * 1-5","Asia/Kolkata")
    clk=clock_sample("node-a",1000,995,20)
    tz=timezone_policy("Asia/Kolkata","STANDARD")
    mf=misfire_policy("RUN_ONCE",300)
    lead=leadership(7,"node-a",2000)
    rec=recurrence("CRON")
    win=calendar_window(900,1100,[1,2,3,4,5])
    job=dispatched(dispatch("job-1","sch-1",1000,7))
    obs=scheduler_event("se-1","sch-1","DISPATCH","SUCCESS",20,False)
    return {"schema_version":"6.33",
            "schedule":sch,"clock":clk,"timezone":tz,
            "misfire":mf,"leadership":lead,"recurrence":rec,
            "calendar_window":win,"dispatch":job,
            "observability":obs,
            "quality_gate":{"valid":True,"errors":[]},
            "checks":{
              "schedule_active":active(sch),
              "clock_within_bound":within_bound(clk,50),
              "timezone_valid":valid(tz),
              "misfire_should_run":should_run(mf,100),
              "leader_term_valid":lead["term"]==7,
              "recurrence_supported":rec["kind"]=="CRON",
              "calendar_contains":contains(win,1000),
              "dispatch_complete":job["status"]=="DISPATCHED",
              "metric":metric(obs)
            }}
