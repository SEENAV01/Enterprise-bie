import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_coverage_plan

def test_valid():
 r=compile_coverage_plan(
  ["o1"],[{"source_id":"s1"}],
  [{"fragment_id":"f1","source_ref":"s1"}],
  [{"target_ref":"o1","status":"COVERED"}],[])
 assert r["quality_gate"]["valid"]

def test_bad_source():
 r=compile_coverage_plan(
  ["o1"],[{"source_id":"s1"}],
  [{"fragment_id":"f1","source_ref":"missing"}],[],[])
 assert not r["quality_gate"]["valid"]
