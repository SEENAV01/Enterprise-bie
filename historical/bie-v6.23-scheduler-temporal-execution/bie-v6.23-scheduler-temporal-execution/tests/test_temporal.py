import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
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

def test_schedule_recurrence_timer_job():
 s=schedule("s","x",10)
 assert active(s)
 assert bounded(recurrence("DAILY",count=2))
 assert due(timer("t","x",20),20)
 assert ready(delayed_job("j","x",30),30)

def test_misfire_lease_window_cancel_retry():
 m=misfire_policy("RUN_NOW")
 assert action(m,True)=="RUN_NOW"
 l=execution_lease("e","w",100)
 assert valid(l,50)
 assert release(l)["status"]=="RELEASED"
 assert inside(execution_window(0,100),50)
 assert complete(cancellation("j","r"))["status"]=="CANCELLED"
 r=temporal_retry(5,"EXPONENTIAL",2)
 assert next_delay(r,3)==8

def test_observability():
 e=temporal_event("e","j","EXECUTE","DONE",10,11,2.5)
 assert metric(e)["latency_ms"]==2.5
