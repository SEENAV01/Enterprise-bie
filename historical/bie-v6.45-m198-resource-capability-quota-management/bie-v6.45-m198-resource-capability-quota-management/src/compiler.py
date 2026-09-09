from resource import resource,active as resource_active
from capability import capability,available as capability_available
from unit import capacity_unit,normalize
from quota import quota,within_limit
from budget import budget,sufficient
from reservation import reservation,activate
from allocation import allocation,allocated
from admission import admission,admitted
from utilization import utilization,saturated
from audit import resource_event,successful
from observability import resource_metric,healthy

def compile_resource_management():
    r=resource("cpu-cluster","COMPUTE",1000,{"region":"primary"})
    c=capability("cap-1","cpu-cluster","CPU", "cores", {"arch":"x86"})
    u=capacity_unit("core",1)
    q=quota("q-1","service-a","cpu-cluster",800,"hour",100)
    b=budget("b-1","service-a","cpu-cluster",900,"hour")
    rs=reservation("res-1","service-a","cpu-cluster",200,
                   "2026-09-01T10:00:00Z","2026-09-01T11:00:00Z")
    rs=activate(rs)
    al=allocation("alloc-1","res-1","cpu-cluster",200)
    ad=admission("service-a","cpu-cluster",200,500,True,True)
    us=utilization("cpu-cluster",500,1000)
    ev=resource_event("re-1","cpu-cluster","ALLOCATE","SUCCESS","service-a")
    met=resource_metric("rm-1","cpu-cluster","ALLOCATE","SUCCESS",
                        us["ratio"],200)
    return {"schema_version":"6.45","resource":r,
            "capability":c,"unit":u,"quota":q,"budget":b,
            "reservation":rs,"allocation":al,"admission":ad,
            "utilization":us,"audit":ev,"observability":met,
            "quality_gate":{"valid":True,"errors":[]},
            "checks":{
              "resource_active":resource_active(r),
              "capability_available":capability_available(c),
              "unit_normalized":normalize(10,u)==10,
              "quota_within_limit":within_limit(q,850),
              "budget_sufficient":sufficient(b,200,100),
              "reservation_active":rs["status"]=="ACTIVE",
              "allocation_valid":allocated(al),
              "admission_granted":admitted(ad),
              "utilization_saturated":saturated(us),
              "audit_success":successful(ev),
              "observability_healthy":healthy(met)
            }}
