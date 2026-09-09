import json
from pathlib import Path
def test_scene_dsl():
 d=json.loads((Path(__file__).parents[1]/"remotion/src/data/electricity-magnetism.scene.json").read_text())
 assert len(d["scenes"])>=18
 assert all(s["source_refs"] and s["duration_frames"]>0 for s in d["scenes"])
