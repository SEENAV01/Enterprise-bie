import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_course
def test_course():
 r=compile_course(
  {"course_id":"c","title":"x","chapters":[{"chapter_id":"ch","lesson_ids":["l"],"order":0}]},
  [{"chapter_id":"ch","lesson_ids":["l"],"order":0}],
  [{"lesson_id":"l","title":"x","order":0}],
  {"l":100})
 assert r["quality_gate"]["valid"]
 assert r["manifest"]["total_duration_frames"]==100
