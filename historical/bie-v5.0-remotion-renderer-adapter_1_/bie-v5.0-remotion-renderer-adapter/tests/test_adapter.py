import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from renderer_adapter import compile_for_remotion
def test_adapter():
 r=compile_for_remotion({
  "fps":30,"duration_s":4,
  "scenes":[{"scene_id":"s","start_s":0,"end_s":4,"objects":[]}]},
  {"src":"a.wav","duration_s":4})
 assert r["schema_version"]=="5.0"
 assert r["composition"]["durationInFrames"]==120
 assert r["render_policy"]["deterministic"]
