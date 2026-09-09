import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_adaptive_plan

def test_selects():
 actions=[
  {"action_id":"a","action_type":"PRACTICE"},
  {"action_id":"b","action_type":"REMEDIATE"}]
 r=compile_adaptive_plan("l",actions,
   signals={"need":1},weights={"need":2},goal="x")
 assert r["decision"]["selected_action"]["action_id"]=="a"

def test_no_actions():
 r=compile_adaptive_plan("l",[],goal="x")
 assert not r["quality_gate"]["valid"]
