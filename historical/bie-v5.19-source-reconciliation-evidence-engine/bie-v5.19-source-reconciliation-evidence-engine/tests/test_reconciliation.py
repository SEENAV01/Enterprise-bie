import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_reconciliation

def test_ready():
 r=compile_reconciliation("c",
  [{"claim_id":"a","concept_refs":["c"]}],
  [{"evidence_id":"e","claim_id":"a","source_id":"s","locator":"p"}])
 assert r["schema_version"]=="5.19"
 assert r["quality_gate"]["valid"]

def test_unresolved():
 r=compile_reconciliation("c",[],[],unresolved=True)
 assert not r["quality_gate"]["valid"]
