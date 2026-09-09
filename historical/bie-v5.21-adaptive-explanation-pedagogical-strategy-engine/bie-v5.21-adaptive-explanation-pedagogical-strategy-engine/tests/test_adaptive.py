import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_adaptive_plan

def test_adaptation():
 r=compile_adaptive_plan(
  {"learner_id":"l","mastery":{"c":0.2},
   "preferences":{"visual_modality":"ANIMATION"}},
  "c","MEDIUM","m1",0.8)
 assert r["quality_gate"]["valid"]
 assert r["strategy"]["explanation_depth"]=="FOUNDATIONAL"
 assert r["strategy"]["intervention"]=="TARGETED"
