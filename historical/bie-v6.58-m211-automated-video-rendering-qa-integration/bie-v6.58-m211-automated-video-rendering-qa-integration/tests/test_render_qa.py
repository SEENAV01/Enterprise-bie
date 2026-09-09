import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))

from render_job import render_job,valid
from renderer_adapter import renderer_adapter
from render_result import render_result,successful
from qa_checks import qa_check,passed
from qa_report import qa_report,passed as report_passed
from retry import retry_policy,should_retry
from manifest import output_manifest,valid as manifest_valid
from provenance import provenance,traceable
from verification import verification,passed as verified

def test_render_and_qa():
    a=renderer_adapter("a","Remotion","6.x")
    j=render_job("j","c","r","output://x.mp4")
    r=render_result("j","SUCCEEDED","output://x.mp4",10,300)
    c=qa_check("q","FILE_EXISTS","output://x.mp4",True,True)
    report=qa_report("rep","j",[c],"PASS")
    m=output_manifest("j",[{"path":"output://x.mp4"}])
    p=provenance("j",["c"],["r"],["rep"])
    v=verification("v","j","PASS")
    assert a["engine"]=="Remotion" and valid(j)
    assert successful(r) and passed(c) and report_passed(report)
    assert manifest_valid(m) and traceable(p) and verified(v)

def test_retry():
    policy=retry_policy(max_attempts=3)
    assert should_retry("TRANSIENT_RENDER_ERROR",1,policy)
    assert not should_retry("TRANSIENT_RENDER_ERROR",3,policy)
