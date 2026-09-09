import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_audio_timeline
def test_compile():
 r=compile_audio_timeline(
  {"text":"define current","duration_s":2,
   "words":[{"word":"define","start_s":0,"end_s":.5},{"word":"current","start_s":.6,"end_s":1}]},
  [{"id":"x","anchor":"current"}],30)
 assert r["duration_frames"]==60
 assert r["policy"]["audio_is_temporal_source_of_truth"]
 assert r["validation"]["valid"]
