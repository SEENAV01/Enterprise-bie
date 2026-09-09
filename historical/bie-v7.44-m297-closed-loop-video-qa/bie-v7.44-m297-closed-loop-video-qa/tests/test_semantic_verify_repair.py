import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))

from semantic_verify_repair import (
    semantic_compare, build_repair_patch, apply_safe_repairs, hash_dsl
)

def test_expected_text_mismatch_creates_grounded_patch():
    dsl={"scenes":[{
        "scene_id":"visual:0001",
        "visuals":[{"type":"equation","text":"F = ma"}]
    }]}
    ocr={"status":"success","frames":[{
        "status":"success","frame":"f.jpg",
        "words":[{"text":"F","confidence":95,"left":1,"top":1,"width":5,"height":5},
                 {"text":"mb","confidence":95,"left":8,"top":1,"width":10,"height":5}]
    }]}
    report=semantic_compare(dsl,ocr)
    assert report["status"]=="mismatch"
    patch=build_repair_patch(dsl,report)
    assert patch["patches"][0]["expected_text"]=="F = ma"

def test_safe_repair_does_not_invent_text():
    dsl={"scenes":[{
        "scene_id":"visual:0001",
        "visuals":[{"type":"equation","text":"F = ma"}]
    }]}
    patch={"patches":[{
        "scene_id":"visual:0001","type":"equation",
        "expected_text":"F = ma","detected_text":"F = mb"
    }]}
    repaired,changed=apply_safe_repairs(dsl,patch)
    assert changed==0
    assert repaired==dsl

def test_hash_is_deterministic():
    d={"scenes":[]}
    assert hash_dsl(d)==hash_dsl(d)
