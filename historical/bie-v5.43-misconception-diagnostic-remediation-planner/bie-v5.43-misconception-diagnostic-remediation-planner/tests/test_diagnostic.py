import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_diagnostic_plan

def test_valid():
 r=compile_diagnostic_plan(
  [{"diagnosis_id":"d1","category":"MISCONCEPTION"}],
  [{"remediation_id":"r1"}],
  {"diagnosis_refs":["d1"],"steps":[],
   "reassessment":{"item_type":"PREDICTION"}})
 assert r["quality_gate"]["valid"]

def test_requires_reassessment():
 r=compile_diagnostic_plan(
  [{"diagnosis_id":"d1","category":"CONCEPT_GAP"}],[],
  {"diagnosis_refs":["d1"],"steps":[]})
 assert not r["quality_gate"]["valid"]
