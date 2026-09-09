
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
from bie_m7.scene import choose_visual, make_scene, compile_scene_to_remotion, compile_lesson

def test_visual():
    assert choose_visual("derivation")=="equation_derivation"
    assert choose_visual("process")=="process_flow"

def test_scene():
    s=make_scene({"id":"x","kind":"definition","source_refs":["p1"]})
    assert s["duration_frames"]==360
    assert s["source_refs"]==["p1"]

def test_compile():
    s=make_scene({"id":"x","kind":"process"})
    c=compile_scene_to_remotion(s)
    assert c["component"]=="BIEScene"
    assert c["props"]["durationInFrames"]==360

def test_lesson():
    scenes=compile_lesson({"sequence":[{"type":"definition","refs":["a"]}]})
    assert len(scenes)==1
