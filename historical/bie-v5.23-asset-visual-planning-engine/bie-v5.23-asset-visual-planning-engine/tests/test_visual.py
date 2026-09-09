import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_visual_plan

def test_visual():
 r=compile_visual_plan("current","DYNAMIC","UNDERSTAND",
   "o1","BEST_FIT",[{"kind":"PARTICLE"}],["book:p31"])
 assert r["quality_gate"]["valid"]
 assert r["visual_spec"]["modality"]=="2D_ANIMATION"

def test_formula():
 r=compile_visual_plan("ohm","FORMULA","UNDERSTAND")
 assert r["visual_spec"]["modality"]=="EQUATION_BUILD"
