import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_grounded_content
def test_grounding():
 r=compile_grounded_content("s",
  [{"evidence_id":"e","source_id":"s","locator":"p1"}],
  [{"claim_id":"c","text":"fact","claim_type":"SOURCE_FACT",
    "required":True,"evidence_ids":["e"],"reasoning_notes":[]}],
  [{"element_id":"v","element_type":"TEXT","claim_ids":["c"],"evidence_ids":["e"]}])
 assert r["quality_gate"]["valid"]
def test_unsupported_blocks():
 r=compile_grounded_content("s",[],
  [{"claim_id":"c","text":"fact","claim_type":"SOURCE_FACT",
    "required":True,"evidence_ids":[]}],[])
 assert not r["quality_gate"]["valid"]
