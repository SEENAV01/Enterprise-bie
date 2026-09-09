import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from trace import span,duration
from metrics import Metrics
from audit import audit_event,valid
from diagnostics import diagnose
def test_observability():
 s=span("s","build"); s["end"]=s["start"]+1
 m=Metrics(); m.inc("done"); m.observe("duration",duration(s))
 a=audit_event("a","system","BUILD","job","PASS")
 d=diagnose([], [s], m.snapshot())
 assert duration(s)==1 and m.counters["done"]==1 and valid(a)
 assert d["health"]=="HEALTHY"
