import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from sli import sli,error_rate
from slo import slo,meets
from error_budget import error_budget,consumed
from burn import burn_rate,exceeds
from alert import alert_rule,evaluate
from incident import incident,resolve
from suppression import suppression,active

def test_sli_slo():
 s=sli("a",999,1000)
 o=slo("a",.99,"a")
 assert meets(o,s["value"])

def test_budget_burn():
 b=error_budget(.99)
 assert b["allowed_error_ratio"]==.01
 assert consumed(1000,5,b)==.5
 assert exceeds(burn_rate(.02,.01),2)

def test_alert_incident():
 r=alert_rule("r","x","bad","CRITICAL")
 assert evaluate(r,{"bad":True})
 i=resolve(incident("i","x","CRITICAL","svc",1),2)
 assert i["status"]=="RESOLVED"

def test_suppression():
 s=suppression("r","maintenance",1,10)
 assert active(s,5)
