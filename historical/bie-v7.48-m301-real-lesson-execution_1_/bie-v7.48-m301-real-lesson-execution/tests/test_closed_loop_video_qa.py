import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))

from closed_loop_video_qa import run_closed_loop, summarize_loop

def test_closed_loop_repairs_then_accepts():
    calls=[]
    def repair(state):
        calls.append("repair")
        return {"status":"success"}
    def rerender(repair_result):
        calls.append("rerender")
        return {"status":"success"}
    def qa(render_result):
        calls.append("qa")
        return {"decision":"accept","status":"success"}
    result=run_closed_loop(
        {"initial":{"decision":"reject"},
         "repair":repair,"rerender":rerender,"qa":qa}, 1
    )
    assert result["status"]=="accepted"
    assert calls==["repair","rerender","qa"]

def test_closed_loop_stops_on_review():
    result=run_closed_loop(
        {"initial":{"decision":"review"},
         "repair":lambda x: {"status":"success"},
         "rerender":lambda x: {"status":"success"},
         "qa":lambda x: {"decision":"accept","status":"success"}}, 1
    )
    assert result["status"]=="review_required"

def test_repair_failure_is_not_silently_accepted():
    result=run_closed_loop(
        {"initial":{"decision":"reject"},
         "repair":lambda x: {"status":"failed"},
         "rerender":lambda x: {"status":"success"},
         "qa":lambda x: {"decision":"accept","status":"success"}}, 1
    )
    assert result["status"]=="repair_failed"
