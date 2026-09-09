import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))

from ocr_text_bbox_qa import analyze_text_boxes, validate_ocr_contract, generate_ocr_repair_plan

def test_ocr_unavailable_is_explicit():
    ocr={"status":"blocked","reason":"TESSERACT_NOT_FOUND","frames":[]}
    report=analyze_text_boxes(ocr)
    plan=generate_ocr_repair_plan(report)
    assert report["passed"] is False
    assert plan["repairs"][0]["action"]=="inspect_text_rendering"

def test_bbox_contract():
    ocr={"status":"success","frames":[{
        "frame":"f.jpg","status":"success",
        "words":[{"text":"Charge","confidence":95,"left":10,"top":20,"width":100,"height":30}]
    }]}
    report=analyze_text_boxes(ocr)
    assert report["passed"] is True
    assert validate_ocr_contract(ocr,report)["passed"] is True
