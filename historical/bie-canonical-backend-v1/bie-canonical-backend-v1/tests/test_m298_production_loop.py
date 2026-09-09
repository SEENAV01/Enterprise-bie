import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))

from production_loop import validate_adapters, run_production_cycle, ProductionLoopError

def adapters_for(decision):
    return {
        "render":lambda p:{"status":"success","mp4":"out.mp4"},
        "frame_sample":lambda r:{"status":"success","frames":["f.jpg"]},
        "ocr":lambda s:{"status":"success","words":["x"]},
        "semantic_qa":lambda p,o:{"decision":decision},
        "repair":lambda p,q:{"status":"success"},
        "regenerate":lambda r:{"status":"success","payload":r.get("payload",{})}
    }

def test_all_adapters_are_required():
    try:
        validate_adapters({})
        assert False
    except ProductionLoopError as e:
        assert "MISSING_PRODUCTION_ADAPTERS" in str(e)

def test_production_loop_accepts():
    result=run_production_cycle(adapters_for("accept"),{},1)
    assert result["status"]=="accepted"

def test_production_loop_reject_then_review():
    result=run_production_cycle(adapters_for("reject"),{},1)
    assert result["status"]=="review_required"

def test_production_loop_reject_then_reruns():
    calls=[]
    a=adapters_for("accept")
    def qa(p,o):
        calls.append("qa")
        return {"decision":"reject"} if len(calls)==1 else {"decision":"accept"}
    a["semantic_qa"]=qa
    a["repair"]=lambda p,q: calls.append("repair") or {"status":"success"}
    a["regenerate"]=lambda r: calls.append("regenerate") or {"status":"success","payload":{}}
    result=run_production_cycle(a,{},1)
    assert result["status"]=="accepted"
    assert calls==["qa","repair","regenerate","qa"]
