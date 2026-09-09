import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from registration import register,registered
from endpoint import endpoint,active
from lease import endpoint_lease,valid
from health import health,routable
from probes import probe,probe_valid
from metadata import service_metadata,has_label
from discovery import discovery_query,matches
from draining import drain,routable as drain_routable
from registry import registry_entry,discoverable
from observability import registry_event,metric

def test_registration_endpoint_lease_health():
 s=register("s","svc","v1")
 e=endpoint("e","127.0.0.1",80)
 assert registered(s) and active(e)
 assert valid(endpoint_lease("e","r",100),50)
 assert routable(health("e"))

def test_probe_metadata_discovery_drain():
 assert probe_valid(probe("e","READINESS",10,3))
 assert has_label(service_metadata("s",{"tier":"api"}),"tier","api")
 s=register("s","svc","v1",region="r1",zone="z1")
 q=discovery_query("svc","v1","r1","z1",True)
 assert matches(q,s,"HEALTHY")
 assert not drain_routable(drain("e"))

def test_registry_observability():
 s=register("s","svc","v1")
 e=endpoint("e","127.0.0.1",80)
 assert discoverable(registry_entry(s,e,"HEALTHY"))
 x=registry_event("x","s","e","REGISTER","OK")
 assert metric(x)["status"]=="OK"
