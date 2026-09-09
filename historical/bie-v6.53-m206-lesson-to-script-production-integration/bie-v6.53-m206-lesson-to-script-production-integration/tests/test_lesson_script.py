import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))

from lesson_input import lesson_input,valid
from script_blocks import block,ordered
from script import script,valid as script_valid
from coverage import coverage,complete
from timing import timing,within_target
from evidence import evidence_check,all_grounded
from provenance import provenance,traceable
from verification import verification,passed

def test_lesson_to_script():
    lesson=lesson_input("l","Lesson",["o"],evidence_ids=["e"])
    blocks=[block("b","EXPLANATION","Explain.",["o"],["e"],1,60)]
    scr=script("s","l",blocks,target_duration_sec=60)
    cov=coverage(lesson["objectives"],scr["blocks"])
    tm=timing(scr["blocks"])
    checks=evidence_check(scr["blocks"])
    p=provenance("s",["l"],["o"],["e"])
    v=verification("v","s","PASS",["e"])
    assert valid(lesson) and script_valid(scr)
    assert complete(cov) and within_target(tm,60)
    assert all_grounded(checks) and traceable(p) and passed(v)

def test_ordering():
    xs=ordered([
        block("b2","SUMMARY","S",["o"],["e"],2),
        block("b1","HOOK","H",["o"],["e"],1)
    ])
    assert [x["block_id"] for x in xs]==["b1","b2"]
