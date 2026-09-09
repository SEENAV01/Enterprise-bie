import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))

from script_compiler import compile_script, validate_script

def test_script_preserves_grounded_source():
    knowledge = {
        "evidence_index": {
            "b1": {"block_id":"b1","text":"Electric charge is a property of matter."}
        }
    }
    plan = {
        "units":[{
            "unit_id":"teach:s1",
            "section_id":"s1",
            "title":"Charge",
            "role":"explanation",
            "source_evidence":["b1"]
        }]
    }
    script=compile_script(plan,knowledge,{"tree":[]})
    assert script["sections"][0]["narration"] == "Electric charge is a property of matter."
    assert script["sections"][0]["source_blocks"] == ["b1"]
    assert validate_script(script,knowledge)["passed"] is True

def test_missing_source_blocks_fail():
    knowledge={"evidence_index":{}}
    script={"sections":[{
        "script_id":"script:s1","narration":"unsupported","grounded":True,
        "source_blocks":["missing"]
    }],"scene_candidates":[]}
    assert validate_script(script,knowledge)["passed"] is False
