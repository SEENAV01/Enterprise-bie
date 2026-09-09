import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from storyboard import build_storyboard
def test_storyboard():
 s=build_storyboard([{"id":"u1","type":"DEFINITION","objective":"x","evidence_ids":["e1"],"text":"X"}])
 assert s["schema_version"]=="3.5"
 assert s["scenes"][0]["scene_type"]=="DEFINITION"
 assert s["scenes"][0]["duration_policy"]=="AUDIO_DRIVEN"
