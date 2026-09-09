import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_renderer_plan

def test_routes():
 contracts=[{"contract_id":"c","representation_type":"ANIMATION"}]
 backends=[
  {"backend_id":"svg","capabilities":["2D_VECTOR"]},
  {"backend_id":"remotion","capabilities":["2D_ANIMATION"]}]
 r=compile_renderer_plan(contracts,backends)
 assert r["jobs"][0]["selected_backend"]=="remotion"

def test_no_backend():
 contracts=[{"contract_id":"c","representation_type":"SIMULATION"}]
 backends=[{"backend_id":"svg","capabilities":["2D_VECTOR"]}]
 r=compile_renderer_plan(contracts,backends)
 assert not r["quality_gate"]["valid"]
