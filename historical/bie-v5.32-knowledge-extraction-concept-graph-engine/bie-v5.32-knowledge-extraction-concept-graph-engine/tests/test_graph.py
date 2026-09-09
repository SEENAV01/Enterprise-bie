import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_knowledge

def test_graph():
 r=compile_knowledge(
  [{"section_id":"s1"}],
  [{"concept_id":"c1","name":"Field"}],
  [],[{"rel_id":"r","source":"c0","target":"c1",
        "relation_type":"PREREQUISITE_OF"}],
  [{"equation_id":"e","formula":"E=F/q"}],[])
 assert r["quality_gate"]["valid"]
 assert r["knowledge_graph"]["concepts"][0]["name"]=="Field"

def test_low_confidence():
 r=compile_knowledge([],[],[],[],
  extraction_records=[{"confidence":0.2}])
 assert not r["quality_gate"]["valid"]
