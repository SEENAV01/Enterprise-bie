import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_integrity_report

def test_supported():
 r=compile_integrity_report(
  [{"claim_id":"c1","source_refs":["s"]}],
  [{"evidence_id":"e1","source_ref":"s","support_level":"SUPPORTED"}])
 assert r["quality_gate"]["valid"]

def test_unsupported():
 r=compile_integrity_report(
  [{"claim_id":"c1","source_refs":["s"]}],
  [{"evidence_id":"e1","source_ref":"x","support_level":"SUPPORTED"}])
 assert not r["quality_gate"]["valid"]

def test_contradiction():
 r=compile_integrity_report([],[],
  [{"claim_a":"a","claim_b":"b","relation":"CONTRADICTS"}])
 assert not r["quality_gate"]["valid"]
