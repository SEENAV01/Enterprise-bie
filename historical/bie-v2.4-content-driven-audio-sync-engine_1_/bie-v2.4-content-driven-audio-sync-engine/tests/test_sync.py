import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from audio_timing import estimate_audio_duration_ms
from presentation_planner import plan_presentation
def test_no_fixed_duration():
 assert estimate_audio_duration_ms("one two three") > 0
 x=plan_presentation({"scene_id":"x","type":"derivation"},5000)
 assert x["timing_policy"]=="CONTENT_DRIVEN_NO_FIXED_MAX_DURATION"
