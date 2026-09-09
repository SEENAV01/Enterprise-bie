import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))

from equation_diagram_qa import (
    classify_text, build_equation_diagram_report,
    generate_equation_diagram_repair_plan,
    validate_equation_diagram_report
)

def test_math_hint_is_classified():
    assert classify_text("F = ma") == "equation_candidate"

def test_report_does_not_fake_semantic_correctness():
    scene={"scenes":[{
        "scene_id":"visual:0001",
        "visuals":[{"type":"equation","text":"F = ma"}]
    }]}
    ocr={"checks":[{"frame":"f.jpg","word_count":3,"low_confidence_word_count":0}]}
    report=build_equation_diagram_report(scene,ocr)
    assert report["semantic_status"] == "not_proven"
    assert validate_equation_diagram_report(report)["passed"] is True
    plan=generate_equation_diagram_repair_plan(report)
    assert plan["repairs"]
