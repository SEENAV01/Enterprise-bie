import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from trace import trace
from span import span,duration
from propagation import context,child_context
from log import log_event,safe_log
from metric import metric
from telemetry import execution_telemetry,latency
from health_signal import health_signal

def test_trace_span():
 t=trace("t","s","op","svc","c","w")
 s=span("s","t",None,"op","svc",1,4)
 assert t["correlation_id"]=="c"
 assert duration(s)==3

def test_propagation():
 c=child_context(context("t","s","c","w"),"s2")
 assert c["trace_id"]=="t" and c["correlation_id"]=="c"

def test_safe_log():
 l=log_event(1,"INFO","x","svc",fields={"token":"secret","x":1})
 assert "token" not in safe_log(l)["fields"]

def test_telemetry_health():
 t=execution_telemetry("task","worker","OK",1,5)
 assert latency(t)==4
 assert health_signal("svc","HEALTHY",1)["status"]=="HEALTHY"
