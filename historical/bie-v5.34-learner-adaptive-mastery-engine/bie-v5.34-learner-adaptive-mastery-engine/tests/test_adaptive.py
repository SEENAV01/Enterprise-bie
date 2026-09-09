import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_adaptive_path

def test_advance():
    r=compile_adaptive_path(
      [{"objective_id":"o1"},{"objective_id":"o2"}],
      [{"objective_id":"o1","status":"UNKNOWN","attempts":0}],
      {"o1":{"evidence_type":"QUIZ","score":0.9}})
    assert r["learner_states"][0]["status"]=="MASTERED"
    assert r["next_objective"]=="o2"
