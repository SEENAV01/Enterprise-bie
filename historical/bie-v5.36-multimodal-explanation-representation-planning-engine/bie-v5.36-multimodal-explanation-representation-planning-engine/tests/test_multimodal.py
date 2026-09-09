import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_multimodal_plan

def test_plan():
 r=compile_multimodal_plan(
  [{"unit_id":"u1","representation_refs":["r1"]}],
  [{"rep_id":"r1","rep_type":"DIAGRAM","priority":1}])
 assert r["quality_gate"]["valid"]

def test_missing():
 r=compile_multimodal_plan(
  [{"unit_id":"u1","representation_refs":["bad"]}],[])
 assert not r["quality_gate"]["valid"]
