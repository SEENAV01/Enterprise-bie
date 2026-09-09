import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_visual_system

def test_system():
 r=compile_visual_system({"style_id":"s"},[{"asset_id":"a"}],
  [{"component_id":"c","asset_refs":["a"]}],
  [{"instance_id":"i","component_id":"c"}])
 assert r["quality_gate"]["valid"]

def test_missing_asset():
 r=compile_visual_system({"style_id":"s"},[],
  [{"component_id":"c","asset_refs":["a"]}],[])
 assert not r["quality_gate"]["valid"]
