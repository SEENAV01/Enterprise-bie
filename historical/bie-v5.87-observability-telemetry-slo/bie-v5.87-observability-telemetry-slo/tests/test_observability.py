import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from metrics import counter,increment
from slis import availability_sli,error_rate,latency_sli
from slo import meets_slo,error_budget
from health import readiness

def test_metrics():
 m=increment(counter("jobs"),2)
 assert m["value"]==2

def test_slis():
 assert availability_sli(99,100)==.99
 assert error_rate(1,100)==.01
 assert latency_sli([1,2,3],2)==2/3

def test_slo():
 assert meets_slo(.999,.999)
 assert error_budget(.999)==.001

def test_health():
 assert readiness({"db":True,"queue":True})
