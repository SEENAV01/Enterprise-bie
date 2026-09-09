import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from cache import cache_entry,present
from ttl import ttl_policy,expired
from invalidation import invalidation,apply
from consistency import consistency_mode,permits_stale
from patterns import cache_pattern,supports
from ownership import state_owner,current
from replication import replication_config,within_lag
from stale_read import stale_read_policy,allowed
from observability import cache_event,metric

def test_cache_ttl_invalidation():
 c=cache_entry("k","v",10)
 assert present(c) and not expired(c,5)
 assert apply(invalidation("k"))["status"]=="INVALIDATED"

def test_consistency_patterns_ownership():
 assert permits_stale(consistency_mode("BOUNDED_STALENESS",10),5)
 p=cache_pattern("x","CACHE_ASIDE","WRITE_THROUGH")
 assert supports(p,"CACHE_ASIDE","WRITE_THROUGH")
 assert current(state_owner("k","n",2))

def test_replication_stale_observability():
 assert within_lag(replication_config("ASYNC",2,10),5)
 assert allowed(stale_read_policy(True,10),5)
 e=cache_event("e","k","GET","HIT",1.0,2)
 assert metric(e)["status"]=="HIT"
