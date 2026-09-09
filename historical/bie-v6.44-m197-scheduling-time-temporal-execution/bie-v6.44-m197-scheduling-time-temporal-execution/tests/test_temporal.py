import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from clock import clock,valid
from schedule import schedule,active
from interval import interval
from calendar import calendar,holiday
from deadline import deadline,valid as deadline_valid
from timeout import timeout,expired
from retry import temporal_retry,allowed
from window import temporal_window,contains
from state import temporal_state,active as state_active

def test_clock_schedule_interval_calendar():
 assert valid(clock())
 assert active(schedule("s"))
 assert interval(5)["every"]==5
 assert holiday(calendar("c",holidays=["2026-01-01"]),"2026-01-01")

def test_deadline_timeout_retry():
 assert deadline_valid(deadline("d","2026-01-01T00:00:00Z"))
 assert expired(timeout(10),10)
 assert allowed(temporal_retry(3),2)

def test_window_state():
 assert contains(temporal_window("2026-01-01","2026-01-02"),"2026-01-01T12:00:00Z")
 assert state_active(temporal_state("r","RUNNING","2026-01-01"),"2026-01-02")
