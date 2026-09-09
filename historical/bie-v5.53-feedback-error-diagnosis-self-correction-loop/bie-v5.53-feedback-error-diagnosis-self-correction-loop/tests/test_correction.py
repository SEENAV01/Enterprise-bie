import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_correction

def test_representation_routes():
 d={"diagnosis_id":"d","error_type":"REPRESENTATION",
    "severity":"MAJOR","confidence":.9}
 r=compile_correction(d,[{"cause_id":"c","confidence":.9}],{})
 assert r["correction_plan"]["action_type"]=="CHANGE_REPRESENTATION"

def test_guard_stops():
 d={"diagnosis_id":"d","error_type":"RENDERER",
    "severity":"MAJOR","confidence":.9}
 r=compile_correction(d,[],{},iteration=3)
 assert not r["quality_gate"]["valid"]
