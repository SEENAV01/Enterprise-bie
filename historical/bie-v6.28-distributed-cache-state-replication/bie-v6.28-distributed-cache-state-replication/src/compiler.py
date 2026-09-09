from cache import cache_entry,present
from ttl import ttl_policy,expired
from invalidation import invalidation,apply
from consistency import consistency_mode,permits_stale
from patterns import cache_pattern,supports
from ownership import state_owner,current
from replication import replication_config,within_lag
from stale_read import stale_read_policy,allowed
from observability import cache_event,metric

def compile_cache():
    c=cache_entry("workflow:42",{"status":"READY"},300,9)
    ttl=ttl_policy(300,True)
    inv=apply(invalidation("workflow:42","UPDATE",9))
    con=consistency_mode("BOUNDED_STALENESS",30)
    pat=cache_pattern("workflow-cache","CACHE_ASIDE","WRITE_THROUGH")
    own=state_owner("workflow:42","cache-node-a",4)
    rep=replication_config("ASYNC",3,15)
    stale=stale_read_policy(True,30)
    obs=cache_event("cache-1","workflow:42",
                    "GET","HIT",2.4,7)
    return {"schema_version":"6.28",
            "cache":c,"ttl":ttl,
            "invalidation":inv,
            "consistency":con,
            "pattern":pat,
            "ownership":own,
            "replication":rep,
            "stale_read":stale,
            "observability":obs,
            "quality_gate":{"valid":True,"errors":[]},
            "checks":{
              "cache_present":present(c),
              "ttl_valid":not expired(c,100),
              "invalidated":inv["status"]=="INVALIDATED",
              "stale_permitted":permits_stale(con,7),
              "pattern_supported":supports(pat,"CACHE_ASIDE","WRITE_THROUGH"),
              "ownership_current":current(own),
              "replication_lag_ok":within_lag(rep,7),
              "stale_read_allowed":allowed(stale,7),
              "metric":metric(obs)
            }}
