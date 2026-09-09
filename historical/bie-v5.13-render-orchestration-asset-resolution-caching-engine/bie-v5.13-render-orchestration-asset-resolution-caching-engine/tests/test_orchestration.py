import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_orchestration
def test_cache_and_assets():
 r=compile_orchestration(
  [{"scene_id":"s","asset_refs":[{"asset_id":"a"}]}],
  [{"asset_id":"a","version":"1"}])
 assert r["quality_gate"]["valid"]
 assert r["render_jobs"][0]["status"]=="READY"
def test_missing_asset():
 r=compile_orchestration(
  [{"scene_id":"s","asset_refs":[{"asset_id":"missing"}]}],[])
 assert not r["quality_gate"]["valid"]
