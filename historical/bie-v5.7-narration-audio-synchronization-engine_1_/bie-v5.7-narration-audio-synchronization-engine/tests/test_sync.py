import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_audio_lesson
def test_timeline():
 r=compile_audio_lesson(
  [{"segment_id":"s","text":"This is a concept.","purpose":"EXPLAIN","visual_ids":["v"]}],
  [{"cue_id":"c","segment_id":"s","trigger":"start","target_ids":["v"],"offset_frames":5}])
 assert r["quality_gate"]["valid"]
 assert r["timeline"]["duration_frames"]>0
