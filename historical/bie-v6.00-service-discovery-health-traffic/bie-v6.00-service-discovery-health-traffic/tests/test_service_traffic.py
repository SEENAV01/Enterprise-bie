import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from registry import service,register
from health import health_probe,healthy,ready
from discovery import discover
from routing import eligible,weighted_choice
from circuit import circuit,record_failure,allow
from drain import drain,can_receive_new_traffic

def test_registry_discovery():
 r=register({},service("svc","v1","a","x"))
 assert len(discover(r,"svc"))==1

def test_health():
 p=health_probe("a","READINESS",1,"READY")
 assert ready(p)
 p=health_probe("a","LIVENESS",1,"HEALTHY")
 assert healthy(p)

def test_routing():
 a=service("s","v1","a","a")
 a["status"]="HEALTHY"
 assert eligible([a],{"a":"HEALTHY"})
 assert weighted_choice([a],0)["instance_id"]=="a"

def test_circuit():
 c=circuit("x",2)
 c=record_failure(c); c=record_failure(c)
 assert not allow(c)

def test_drain():
 d=drain("a",1)
 assert not can_receive_new_traffic(d)
