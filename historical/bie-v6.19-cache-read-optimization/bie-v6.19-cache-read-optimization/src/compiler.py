from cache_key import cache_key,valid
from ttl import ttl_policy,expired
from invalidation import invalidation,complete
from consistency import consistency_mode,acceptable
from read_through import read_through,miss
from write_through import write_through,write
from materialized_view import materialized_view,refresh
from stampede import stampede_policy,protected
from observability import cache_event,metric

def compile_cache():
    key=cache_key("bie","workflow",
                  "wf-42",3,"tenant-a")
    ttl=ttl_policy("workflow-cache",60,30)
    inv=complete(invalidation(key,
                              "entity-updated","EXACT"))
    cons=consistency_mode("workflow-cache",
                          "READ_YOUR_WRITES")
    rt=read_through("workflow-cache",key,
                    "workflow-repository")
    wt=write_through("workflow-cache",key,
                     "workflow-repository")
    view=refresh(materialized_view(
        "active-workflows",["workflow"],"EVENT"))
    stamp=stampede_policy("workflow-cache",
                          "SINGLE_FLIGHT",100)
    event=cache_event("cache-1",
                      "workflow-cache",key,
                      "GET",True,4.2)
    return {"schema_version":"6.19",
            "cache_key":key,
            "ttl_policy":ttl,
            "invalidation":inv,
            "consistency":cons,
            "read_through":rt,
            "write_through":wt,
            "materialized_view":view,
            "stampede_policy":stamp,
            "observability":event,
            "quality_gate":{"valid":True,"errors":[]},
            "checks":{
              "key_valid":valid(key),
              "expired":expired(0,30,60),
              "invalidation_complete":
                   inv["status"]=="COMPLETED",
              "consistency_acceptable":
                   acceptable(cons,
                              {"EVENTUAL",
                               "READ_YOUR_WRITES",
                               "STRONG"}),
              "read_miss":miss(rt)["action"],
              "write_action":write(wt)["action"],
              "stampede_protected":protected(stamp),
              "metric":metric(event)
            }}
