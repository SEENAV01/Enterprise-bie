
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parents[1]))
from bie.stages.m5_verify import run
from bie.stages.m7_scene import run as scene_run

def test_m5_pass():
    x={"units":[{"id":"u","source_refs":["p1"]}],
       "frontier":{"backward":[],"forward":[],"application":[]}}
    assert run(x)["decision"]=="PASS"

def test_m5_review():
    x={"units":[{"id":"u","source_refs":[]}],
       "frontier":{"backward":[{"id":"x"}],"forward":[],"application":[]}}
    assert run(x)["decision"]=="REVIEW"

def test_scene():
    x={"sequence":[{"type":"concept","refs":["u"],"source_refs":["p1"]}]}
    assert scene_run(x)["scenes"][0]["duration_frames"]==360
