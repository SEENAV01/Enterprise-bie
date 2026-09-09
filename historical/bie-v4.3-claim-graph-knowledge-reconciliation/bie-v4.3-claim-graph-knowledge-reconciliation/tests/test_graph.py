import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from knowledge_graph import build_graph
def test_graph():
 r=build_graph(
  [{"id":"x","label":"X"}],
  [{"id":"c1","text":"same claim","source_quality":1,"evidence_ids":["s1"]},
   {"id":"c2","text":"same claim","source_quality":.9,"evidence_ids":["s2"]}],
  [{"source_id":"s1","title":"S1"},{"source_id":"s2","title":"S2"}])
 assert r["schema_version"]=="4.3"
 assert len([n for n in r["nodes"] if n["type"]=="CLAIM"])==1
