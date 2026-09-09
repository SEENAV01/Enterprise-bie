import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from api import compile_scene
def test_orchestrator():
 r=compile_scene({
  "scene_id":"s",
  "objects":[{"id":"a","kind":"TEXT","content":"A","role":"PRIMARY","width":300,"height":100}],
  "events":[{"event_id":"e","frame":0,"end_frame":30}]},["a"])
 assert r["schema_version"]=="5.2"
 assert r["validation"]["valid"]
 assert r["focus_plan"][0]["emphasis"]
