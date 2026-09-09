from registration import register,registered
from endpoint import endpoint,active
from lease import endpoint_lease,valid
from health import health,routable as healthy
from probes import probe,probe_valid
from metadata import service_metadata,has_label
from discovery import discovery_query,matches
from draining import drain,routable as not_draining
from registry import registry_entry,discoverable
from observability import registry_event,metric

def compile_registry():
    svc=register("svc-1","workflow-service","v1",
                 {"team":"platform"},"ap-south-1","zone-a")
    ep=endpoint("ep-1","10.0.0.10",8080,
                "HTTP",{"weight":100})
    lease=endpoint_lease("ep-1","registry-1",500,4)
    h=health("ep-1","HEALTHY",8.2,400)
    pr=probe("ep-1","READINESS",10,3)
    md=service_metadata("svc-1",{"tier":"backend"},
                        {"owner":"platform"})
    q=discovery_query("workflow-service","v1",
                      "ap-south-1","zone-a",True)
    dr=drain("ep-1","DECOMMISSION",600)
    entry=registry_entry(svc,ep,"HEALTHY")
    obs=registry_event("reg-1","svc-1","ep-1",
                       "REGISTER","SUCCESS",
                       "ap-south-1","zone-a")
    return {"schema_version":"6.27",
            "service":svc,"endpoint":ep,
            "lease":lease,"health":h,
            "probe":pr,"metadata":md,
            "discovery":q,"draining":dr,
            "registry_entry":entry,
            "observability":obs,
            "quality_gate":{"valid":True,"errors":[]},
            "checks":{
              "registered":registered(svc),
              "endpoint_active":active(ep),
              "lease_valid":valid(lease,400),
              "healthy":healthy(h),
              "probe_valid":probe_valid(pr),
              "metadata_label":has_label(md,"tier","backend"),
              "discovery_match":matches(q,svc,"HEALTHY"),
              "draining_blocks":not not_draining(dr),
              "discoverable":discoverable(entry),
              "metric":metric(obs)
            }}
