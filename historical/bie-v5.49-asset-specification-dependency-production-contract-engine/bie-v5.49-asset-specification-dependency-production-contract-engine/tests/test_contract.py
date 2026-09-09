import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_production_system

def test_valid():
 assets=[{"asset_id":"a"}]
 contracts=[{"asset_ref":"a","outputs":["x"],"validation":["render"]}]
 r=compile_production_system(assets,contracts,["a"],[])
 assert r["quality_gate"]["valid"]

def test_bad_dependency():
 r=compile_production_system(
  [{"asset_id":"a"}],
  [{"asset_ref":"a","outputs":["x"],"validation":["render"]}],
  ["a"],[{"source_id":"a","target_id":"missing"}])
 assert not r["quality_gate"]["valid"]
