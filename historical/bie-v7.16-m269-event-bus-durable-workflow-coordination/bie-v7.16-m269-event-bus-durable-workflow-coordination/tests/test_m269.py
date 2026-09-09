import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from events import make_event
from ordering import ordering_errors
from delivery import deliver_once
from workflow import trigger_workflow
def test_m269():
 e=make_event("e","X","a",1)
 assert not ordering_errors([e])
 s={}; assert deliver_once(s,e,"c")["delivered"]
 assert deliver_once(s,e,"c")["duplicate"]
 assert trigger_workflow(e,[{"event_type":"X","workflow":"W"}])[0]["workflow"]=="W"
