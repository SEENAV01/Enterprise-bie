import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_curriculum

def test_curriculum():
 r=compile_curriculum("c",[],[{"concept_id":"a"},{"concept_id":"b"}],
  [{"from_concept":"a","to_concept":"b"}],[],[])
 assert r["quality_gate"]["valid"]
 assert r["concept_order"]==["a","b"]

def test_cycle():
 r=compile_curriculum("c",[],[{"concept_id":"a"},{"concept_id":"b"}],
  [{"from_concept":"a","to_concept":"b"},{"from_concept":"b","to_concept":"a"}],[],[])
 assert not r["quality_gate"]["valid"]
