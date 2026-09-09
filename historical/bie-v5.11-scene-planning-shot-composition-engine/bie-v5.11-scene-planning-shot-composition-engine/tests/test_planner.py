import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_scene_plan
def test_plan():
 r=compile_scene_plan(
  [{"objective_id":"o","statement":"Explain"}],
  [{"segment_id":"s","purpose":"EXPLAIN","text":"hello",
    "timing":{"start_frame":0,"end_frame":30}}],
  [{"visual_id":"v","narration_cues":["s"]}],
  [],{"style_id":"s"},{"grammar_id":"g"})
 assert r["quality_gate"]["valid"]
 assert r["shots"][0]["timing"]["end_frame"]==30
