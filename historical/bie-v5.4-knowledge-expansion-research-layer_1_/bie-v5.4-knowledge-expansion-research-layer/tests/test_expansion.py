import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_expansions
def test_expansion():
 r=compile_expansions(
  [{"expansion_id":"x","source_claim_ids":["c"],"kind":"HIGHER_ORDER",
    "title":"Deep concept","rationale":"r","confidence":.5}],
  {"x":{"sources":[{"authority":1,"primary":True,"recency_score":1}]}})
 assert r["quality_gate"]["valid"]
 assert r["nodes"][0]["support_class"]=="EXTERNAL_OR_DERIVED"
def test_unsupported():
 r=compile_expansions(
  [{"expansion_id":"x","source_claim_ids":["c"],"kind":"MODERN_CONTEXT",
    "title":"Modern","rationale":"r"}],{})
 assert not r["quality_gate"]["valid"]
