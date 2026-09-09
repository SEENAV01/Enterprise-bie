import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))

from visual_qa import inspect_render, generate_repair_plan, validate_visual_qa

def test_missing_render_creates_repair_plan():
    report=inspect_render({"rendered":False,"output":"/tmp/missing.mp4"})
    plan=generate_repair_plan({},report)
    assert report["passed"] is False
    assert plan["repairs"][0]["action"]=="rerender"
    assert validate_visual_qa(report,plan)["passed"] is True

def test_nonempty_artifact_passes_basic_inspection(tmp_path):
    p=tmp_path/"x.mp4"
    p.write_bytes(b"fake")
    report=inspect_render({"rendered":True,"output":str(p)})
    assert report["metrics"]["file_size_bytes"] == 4
