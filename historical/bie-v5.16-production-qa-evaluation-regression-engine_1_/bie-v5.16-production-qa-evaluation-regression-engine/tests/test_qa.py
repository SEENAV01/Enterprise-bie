import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_qa

def test_pass():
    scene={"scene_id":"s","duration_in_frames":30,
           "layers":[{"layer_id":"x"}],
           "animations":[{"target_id":"x","keyframes":[{"frame":0},{"frame":5}]}],
           "captions":[{"start_frame":0,"end_frame":30}]}
    r=compile_qa([scene],[{"width":1920,"height":1080,"fps":30,"duration_frames":30}],[])
    assert r["quality_gate"]["passed"]

def test_bad_caption():
    scene={"scene_id":"s","duration_in_frames":30,
           "layers":[],"animations":[],"captions":[{"start_frame":20,"end_frame":10}]}
    r=compile_qa([scene])
    assert not r["quality_gate"]["passed"]
