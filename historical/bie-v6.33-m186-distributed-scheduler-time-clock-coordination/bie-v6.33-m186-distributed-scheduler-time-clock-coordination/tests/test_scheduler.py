import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from schedule import schedule,active
from clock import clock_sample,within_bound
from timezone import timezone_policy,valid
from misfire import misfire_policy,should_run
from leader import leadership,valid as leader_valid
from recurrence import recurrence,bounded
from calendar_window import calendar_window,contains
from dispatch import dispatch,dispatched
from observability import scheduler_event,metric

def test_schedule_clock_timezone():
 assert active(schedule("s","0 9 * * *"))
 assert within_bound(clock_sample("a",1,1,10),20)
 assert valid(timezone_policy("Asia/Kolkata"))

def test_misfire_leader_recurrence():
 assert should_run(misfire_policy("RUN_ONCE",10),20)
 assert leader_valid(leadership(2,"a"),2)
 assert bounded(recurrence("INTERVAL",60,count=3))

def test_window_dispatch_observability():
 w=calendar_window(1,10,[1])
 assert contains(w,5)
 assert dispatched(dispatch("j","s",5,2))["status"]=="DISPATCHED"
 e=scheduler_event("e","s","FIRE","OK",4,False)
 assert metric(e)["clock_skew_ms"]==4
