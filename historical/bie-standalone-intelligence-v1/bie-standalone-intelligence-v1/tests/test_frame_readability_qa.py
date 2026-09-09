import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))

from frame_readability_qa import build_readability_report, generate_readability_repair_plan

def test_missing_frames_fail_and_create_review_plan():
    sampling={"status":"blocked","reason":"FFMPEG_NOT_FOUND","frames":[]}
    readability={"status":"blocked","reason":"PIL_NOT_FOUND","checks":[]}
    report=build_readability_report(sampling,readability)
    plan=generate_readability_repair_plan(report)
    assert report["passed"] is False
    assert plan["repairs"][0]["action"]=="install_runtime_dependency"

def test_valid_frame_metadata_passes():
    sampling={"status":"success","frames":["frame-01.jpg"]}
    readability={"status":"success","checks":[{
        "frame":"frame-01.jpg","width":1920,"height":1080,
        "pixels":1920*1080,"readability_status":"image_available_for_review"
    }]}
    report=build_readability_report(sampling,readability)
    assert report["passed"] is True
    assert report["sample_count"] == 1
