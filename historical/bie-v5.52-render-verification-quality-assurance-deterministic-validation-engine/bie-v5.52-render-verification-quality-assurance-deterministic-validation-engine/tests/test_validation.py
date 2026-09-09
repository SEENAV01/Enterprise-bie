import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_validation

def test_accept():
 c={"acceptance":{"required_checks":["a","b"]}}
 r=compile_validation({"asset_id":"x"},c,
  [{"check_id":"a","status":"PASS"},
   {"check_id":"b","status":"PASS"}])
 assert r["quality_gate"]["accepted"]

def test_fail():
 c={"acceptance":{"required_checks":["a"]}}
 r=compile_validation({"asset_id":"x"},c,
  [{"check_id":"a","status":"FAIL"}])
 assert not r["quality_gate"]["accepted"]
