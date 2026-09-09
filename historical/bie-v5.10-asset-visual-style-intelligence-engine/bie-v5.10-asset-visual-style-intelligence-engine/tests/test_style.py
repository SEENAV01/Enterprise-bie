import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_visual_system
def test_valid():
 r=compile_visual_system(
  {"style_id":"s","name":"x"},
  {"grammar_id":"g"},
  [{"asset_id":"a","asset_type":"ICON","semantic_role":"x"}],
  [{"scene_id":"1","style_id":"s","visual_grammar_id":"g",
    "asset_refs":[{"asset_id":"a"}]}])
 assert r["quality_gate"]["valid"]
def test_unknown_asset():
 r=compile_visual_system(
  {"style_id":"s","name":"x"},{"grammar_id":"g"},[],
  [{"scene_id":"1","style_id":"s","visual_grammar_id":"g",
    "asset_refs":[{"asset_id":"missing"}]}])
 assert not r["quality_gate"]["valid"]
