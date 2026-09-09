import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_shot_plan
def test_compile():
    r=compile_shot_plan([{"shot_id":"s","timing":{"start_frame":0,"end_frame":30}}],
                        [{"shot_id":"s","layer_id":"x","component":"TEXT","props":{"text":"Hi"}}])
    assert r["quality_gate"]["valid"]
    assert r["remotion"][0]["composition"]["durationInFrames"]==30
