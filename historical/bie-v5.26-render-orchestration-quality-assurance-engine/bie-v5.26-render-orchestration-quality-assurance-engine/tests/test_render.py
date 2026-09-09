import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_render_plan

def test_preflight():
 r=compile_render_plan("p","Root.tsx","s",["a"],["a"],
   {"x":1},10,30,300,10)
 assert r["release_gate"]["release"]

def test_missing_asset():
 r=compile_render_plan("p","Root.tsx","s",["a"],[],
   {"x":1},10,30,300,10)
 assert not r["release_gate"]["release"]
