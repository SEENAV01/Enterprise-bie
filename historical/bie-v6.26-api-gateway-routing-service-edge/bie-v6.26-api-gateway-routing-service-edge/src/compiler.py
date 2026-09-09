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

def compile_gateway():
    r=route("r-1","/v1/workflows","GET",
            "workflow-service","v1")
    v=api_version("v1","PATH","/v1",True)
    a=auth_handoff("BEARER","identity:user-1",["workflow:read"])
    rl=rate_limit("tenant-a:user-1",100,60)
    tr=transform("request-normalize",
                 {"x-request-id":"req-1"},{"x-gateway":"bie"})
    up=upstream("workflow-service",
                ["worker-a","worker-b"],"ROUND_ROBIN")
    h=health("worker-a","HEALTHY",12.1)
    rt=gateway_retry(2,"EXPONENTIAL",["502","503","504"])
    cb=circuit_breaker("workflow-service",5,30)
    obs=edge_event("edge-1","r-1","PROXY",
                   "SUCCESS","worker-a",18.4)
    return {"schema_version":"6.26",
            "route":r,"versioning":v,
            "auth_handoff":a,"rate_limit":rl,
            "transform":tr,"upstream":up,
            "health":h,"retry":rt,
            "circuit_breaker":cb,
            "observability":obs,
            "quality_gate":{"valid":True,"errors":[]},
            "checks":{
              "route_matches":matches(r,"/v1/workflows","GET"),
              "version_selected":selected(v,"/v1"),
              "authorized":authorized(a,"workflow:read"),
              "rate_limit_ok":within(rl,75),
              "transform_header":header_present(tr,"x-request-id"),
              "upstream_selected":choose(up,0)=="worker-a",
              "healthy_routable":routable(h),
              "retry_503":should_retry(rt,"503",1),
              "circuit_allows":allows(cb),
              "metric":metric(obs)
            }}
