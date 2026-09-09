from scene import scene,valid as scene_valid,ordered
from storyboard import storyboard,valid as storyboard_valid
from visual_plan import visual,valid as visual_valid
from narration import narration_link,valid as narration_valid
from timing import timeline,validate_continuity
from coverage import scene_coverage,complete
from evidence import evidence_map,grounded
from provenance import provenance,traceable
from verification import verification,passed

def build_storyboard():
    objectives=["obj-charge","obj-force"]

    scenes=ordered([
        scene("sc1","TITLE","Introduce the lesson",
              ["b1"],objectives[:1],20,1),
        scene("sc2","EXPLANATION","Explain charge",
              ["b3"],["obj-charge"],55,2),
        scene("sc3","DIAGRAM","Visualize force direction",
              ["b4"],["obj-force"],50,3),
        scene("sc4","QUESTION","Check understanding",
              ["b5"],["obj-force"],35,4),
        scene("sc5","SUMMARY","Connect the two concepts",
              ["b6"],objectives,35,5)
    ])

    sb=storyboard("storyboard-1","script-1",scenes)

    visuals=[
        visual("v1","TEXT","Lesson title and framing","sc1"),
        visual("v2","DIAGRAM","Charge interaction diagram","sc3",
               "asset://electric-force-diagram",
               {"type":"DRAW_ON"}),
        visual("v3","TEXT","Question prompt","sc4"),
        visual("v4","DIAGRAM","Concept relationship summary","sc5")
    ]

    links=[
        narration_link("n1","sc1",["b1"],0,20),
        narration_link("n2","sc2",["b3"],20,75),
        narration_link("n3","sc3",["b4"],75,125),
        narration_link("n4","sc4",["b5"],125,160),
        narration_link("n5","sc5",["b6"],160,195)
    ]

    cov=scene_coverage(objectives,scenes)
    tl=timeline(scenes)
    ev=evidence_map("sc3",["ev-force"],["record-figure-1"])
    prov=provenance("storyboard-1",["script-1"],["lesson-1"],
                    ["ev-charge","ev-force"],
                    ["artifact://lesson-plan"])
    check=verification("verify-1","storyboard-1","PASS",
                       ["ev-charge","ev-force"])

    return {
        "schema_version":"6.54","storyboard":sb,"visuals":visuals,
        "narration_links":links,"coverage":cov,"timeline":tl,
        "evidence":ev,"provenance":prov,"verification":check,
        "quality_gate":{"valid":(
            storyboard_valid(sb)
            and all(scene_valid(s) for s in scenes)
            and all(visual_valid(v) for v in visuals)
            and all(narration_valid(n) for n in links)
            and validate_continuity(scenes)
            and complete(cov) and grounded(ev)
            and traceable(prov) and passed(check)
        ),"errors":[]}
    }
