import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))

from scene import scene,ordered,valid
from storyboard import storyboard
from visual_plan import visual
from narration import narration_link
from coverage import scene_coverage,complete
from timing import timeline,validate_continuity
from evidence import evidence_map,grounded
from provenance import provenance,traceable
from verification import verification,passed

def test_storyboard_pipeline():
    scenes=ordered([
        scene("s2","DIAGRAM","Diagram",["b2"],["o"],2,30),
        scene("s1","EXPLANATION","Explain",["b1"],["o"],1,30)
    ])
    sb=storyboard("sb","script",scenes)
    vs=visual("v","DIAGRAM","A diagram","s1")
    nl=narration_link("n","s1",["b1"],0,30)
    cov=scene_coverage(["o"],scenes)
    ev=evidence_map("s1",["e"])
    p=provenance("sb",["script"],["lesson"],["e"])
    ver=verification("v","sb","PASS",["e"])
    assert storyboard(sb)["storyboard_id"]=="sb"
    assert valid(vs if False else scenes[0])
    assert vs["scene_id"]=="s1" and nl["script_block_ids"]==["b1"]
    assert complete(cov) and timeline(scenes)["total_duration_sec"]==60
    assert validate_continuity(scenes) and grounded(ev)
    assert traceable(p) and passed(ver)
