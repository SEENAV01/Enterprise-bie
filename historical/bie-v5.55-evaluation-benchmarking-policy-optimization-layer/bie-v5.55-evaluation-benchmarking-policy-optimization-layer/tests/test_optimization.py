import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_optimization

def test_bounded_low_confidence():
 r=compile_optimization([],[],[
  {"recommendation_id":"r","policy_ref":"p",
   "action":"CHANGE","confidence":.3}])
 assert r["recommendations"][0]["action"]=="HUMAN_REVIEW"

def test_unapproved_change_blocked():
 r=compile_optimization([],[],[],[
  {"change_id":"c","policy_ref":"p","scope":"LOCAL",
   "evidence_refs":["e"],"approval_required":True}],[])
 assert not r["quality_gate"]["valid"]
