import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from route import route,matches
from versioning import api_version,selected
from auth_handoff import auth_handoff,authorized
from rate_limit import rate_limit,within
from transform import transform,header_present
from upstream import upstream,choose
from health import health,routable
from retry import gateway_retry,should_retry
from circuit_breaker import circuit_breaker,allows
from observability import edge_event,metric

def test_route_version_auth_limits():
 r=route("r","/x","GET","u","v1")
 assert matches(r,"/x","GET")
 assert selected(api_version("v1","PATH","/v1",True),"/v1")
 assert authorized(auth_handoff("BEARER",scopes=["read"]),"read")
 assert within(rate_limit("k",10,60),10)

def test_transform_upstream_health_retry_cb():
 t=transform("t",{"x":"1"})
 assert header_present(t,"x")
 assert choose(upstream("u",["a","b"]),1)=="b"
 assert routable(health("a"))
 assert should_retry(gateway_retry(2),"503",1)
 assert allows(circuit_breaker("c"))

def test_observability():
 e=edge_event("e","r","PROXY","OK","a",1.5)
 assert metric(e)["route_id"]=="r"
