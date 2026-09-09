import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_long_form_timeline
def test_sync():
 r=compile_long_form_timeline(
  [{"segment_id":"n","start_frame":0,"end_frame":100}],
  [{"beat_id":"b","segment_id":"n","trigger":"X","start_frame":20,"end_frame":80}],
  [{"caption_id":"c","text":"x","start_frame":0,"end_frame":100}])
 assert r["quality_gate"]["valid"]
 assert r["timeline"]["duration_frames"]==100
def test_bad_sync():
 r=compile_long_form_timeline(
  [{"segment_id":"n","start_frame":0,"end_frame":100}],
  [{"beat_id":"b","segment_id":"n","trigger":"X","start_frame":120}],
  [])
 assert not r["quality_gate"]["valid"]
