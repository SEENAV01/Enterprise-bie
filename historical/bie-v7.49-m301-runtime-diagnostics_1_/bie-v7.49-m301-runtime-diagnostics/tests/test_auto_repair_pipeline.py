import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))

from auto_repair_pipeline import apply_repair_and_prepare

def test_repair_is_grounded_and_changes_only_mismatch():
    dsl={"scenes":[{
        "scene_id":"visual:0001",
        "visuals":[{"type":"equation","text":"F = ma"}]
    }]}
    report={"repair_patch":{"patches":[{
        "scene_id":"visual:0001","type":"equation",
        "expected_text":"F = ma","detected_text":"F = mb"
    }]}}
    result=apply_repair_and_prepare(dsl,report)
    assert result["changed"]==0
    assert result["scene_dsl"]==dsl

def test_no_patch_means_no_change():
    dsl={"scenes":[]}
    result=apply_repair_and_prepare(dsl,{"repair_patch":{"patches":[]}})
    assert result["changed"]==0
    assert result["status"] if "status" in result else True
