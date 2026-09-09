import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))

from layer import layer
from composition import composition,valid
from caption import caption
from transition import transition
from sync import sync_point
from render import render_profile
from provenance import provenance,traceable
from verification import verification,passed

def test_video_composition():
    ls=[layer("l","VISUAL","asset://x",0,10,1)]
    c=composition("c","sb",ls,1920,1080,30,10)
    cap=caption("cap","Hello",0,2)
    tr=transition("t","FADE",2,.5)
    sy=sync_point("s","sc","n",["a"],0,2)
    rp=render_profile("r")
    p=provenance("c",["sb"],["a"],["audio"],["sc"])
    v=verification("v","c","PASS")
    assert valid(c) and cap["end_sec"]==2
    assert tr["transition_type"]=="FADE" and sy["scene_id"]=="sc"
    assert rp["format"]=="MP4" and traceable(p) and passed(v)
