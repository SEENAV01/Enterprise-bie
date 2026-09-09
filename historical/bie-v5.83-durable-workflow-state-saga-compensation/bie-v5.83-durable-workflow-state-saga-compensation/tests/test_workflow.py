import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from state import transition,workflow
from checkpoint import checkpoint,latest
from saga import compensation_plan
from recovery import recovery_action
from timeouts import timeout

def test_state():
 assert transition("PENDING","RUNNING")=="RUNNING"

def test_checkpoint():
 a=checkpoint("w","RUNNING",["a"],sequence=1)
 b=checkpoint("w","RUNNING",["a","b"],sequence=2)
 assert latest([a,b])["sequence"]==2

def test_compensation():
 steps=[{"step_id":"a","compensation":"undo-a"},
        {"step_id":"b","compensation":"undo-b"}]
 assert compensation_plan(steps,["a","b"])==["undo-b","undo-a"]

def test_timeout():
 assert timeout({"timeout_seconds":5},5)
