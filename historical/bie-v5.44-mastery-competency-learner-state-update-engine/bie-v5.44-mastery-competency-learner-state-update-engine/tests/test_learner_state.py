import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_learner_state

def test_state():
 events=[
  {"evidence_id":"e1","objective_ref":"o1","score":.8,"confidence":1},
  {"evidence_id":"e2","objective_ref":"o1","score":1.0,"confidence":.5}]
 r=compile_learner_state("l",events,["o1"])
 assert r["objective_states"]["o1"]["evidence_count"]==2
 assert r["quality_gate"]["valid"]
