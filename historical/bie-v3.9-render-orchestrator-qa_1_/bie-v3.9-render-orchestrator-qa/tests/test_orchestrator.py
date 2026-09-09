import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from orchestrator import prepare_render,run_qa
def test_incremental():
 scenes=[{"scene_id":"s1","duration":{"mode":"AUDIO_DRIVEN"},"narration_unit_ids":["u1"],"layers":[{"type":"Text"}]}]
 r=prepare_render(scenes,{}, {})
 assert r["render_scene_ids"]==["s1"]
def test_qa():
 scenes=[{"scene_id":"s1","duration":{"mode":"AUDIO_DRIVEN"},"narration_unit_ids":["u1"],"layers":[{"type":"Text"}]}]
 r=run_qa(scenes,{"s1":{"render_failed":False,"audio_missing":False,"overflow_detected":False}})
 assert r["course"]["status"]=="PASS"
