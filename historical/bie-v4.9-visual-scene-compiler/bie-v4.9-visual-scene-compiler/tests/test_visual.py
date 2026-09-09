import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_visual_scenes
def test_visual():
 r=compile_visual_scenes(
  {"fps":30,"duration_s":4,"scenes":[{"scene_id":"s","start_s":0,"end_s":4}]},
  [{"event_id":"e","time_s":1,"kind":"TEXT","content":"hello"}])
 assert r["schema_version"]=="4.9"
 assert r["scenes"][0]["objects"][0]["kind"]=="TEXT"
 assert r["accessibility"]["captions"]
