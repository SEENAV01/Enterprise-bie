import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from fingerprint import fingerprint
from cache import cache_key,cache_put
from invalidation import affected_nodes

def test_fingerprint_deterministic():
 assert fingerprint({"b":2,"a":1})==fingerprint({"a":1,"b":2})

def test_cache():
 c={}
 k=cache_key("SCENE","abc","cfg","p1")
 assert cache_put(c,k,"artifact")==cache_put(c,k,"other")

def test_invalidation():
 nodes=[{"node_id":"a"},{"node_id":"b","depends_on":["a"]},
        {"node_id":"c","depends_on":["b"]}]
 assert affected_nodes(nodes,{"a"})=={"a","b","c"}
