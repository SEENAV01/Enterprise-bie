import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import build_memory_record,reuse_decision

def test_record():
 r=build_memory_record("x","concept",{"a":1},["c"],["src"],"bie","review")
 assert r["version"]=="1.0"
 assert r["provenance"]["source_refs"]==["src"]

def test_reuse():
 records=[{"record_id":"x","concept_refs":["c"]}]
 candidates=[{"record_id":"x","score":0.95,"reason":"semantic match"}]
 r=reuse_decision(records,"c",candidates)
 assert r["decision"]=="REUSE"
