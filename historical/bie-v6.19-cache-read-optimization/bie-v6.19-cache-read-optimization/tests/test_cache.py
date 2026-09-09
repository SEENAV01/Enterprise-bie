import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from cache_key import cache_key,valid
from ttl import ttl_policy,expired
from invalidation import invalidation,complete
from consistency import consistency_mode,acceptable
from read_through import read_through,miss
from write_through import write_through,write
from materialized_view import materialized_view,refresh
from stampede import stampede_policy,protected
from observability import cache_event,metric

def test_key_ttl_invalidation():
 k=cache_key("n","e","1",2,"t")
 assert valid(k) and k.endswith("t:1:2")
 assert not expired(0,5,10)
 assert complete(invalidation(k,"update"))["status"]=="COMPLETED"

def test_patterns():
 c=consistency_mode("c","STRONG")
 assert acceptable(c,{"STRONG"})
 r=read_through("c","k","repo")
 assert miss(r)["action"]=="LOAD_AND_POPULATE"
 w=write_through("c","k","repo")
 assert "BACKING_STORE" in write(w)["action"]
 v=refresh(materialized_view("v",["e"]))
 assert v["last_action"]=="REFRESH"

def test_stampede_observability():
 s=stampede_policy("c","SINGLE_FLIGHT")
 assert protected(s)
 e=cache_event("e","c","k","GET",True,2.1)
 assert metric(e)["hit"] is True
