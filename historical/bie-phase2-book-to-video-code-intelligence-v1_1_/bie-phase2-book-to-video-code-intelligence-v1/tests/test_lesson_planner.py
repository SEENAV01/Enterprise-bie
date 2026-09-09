import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))

from lesson_planner import compile_lesson_plan, validate_lesson_plan

def test_plan_is_grounded_and_ordered():
    knowledge={"evidence_index":{
        "b1":{"block_id":"b1","page":1,"kind":"PARAGRAPH","text":"Charge is a property."},
        "b2":{"block_id":"b2","page":2,"kind":"PARAGRAPH","text":"Charges interact."}
    }}
    structure={"tree":[
        {"section_id":"s1","title":"Charge","level":1,"start_page":1,
         "content_blocks":["b1"],"children":[]},
        {"section_id":"s2","title":"Interaction","level":1,"start_page":2,
         "content_blocks":["b2"],"children":[]}
    ]}
    retrieval={"concept_links":[],"index":{"vectors":{}}}
    plan=compile_lesson_plan(structure,knowledge,retrieval)
    assert [u["section_id"] for u in plan["units"]]==["s1","s2"]
    assert plan["prerequisites"][0]["from"]=="teach:s1"
    assert validate_lesson_plan(plan,knowledge)["passed"] is True

def test_invalid_evidence_blocks_plan():
    knowledge={"evidence_index":{}}
    plan={"units":[{"unit_id":"u","source_evidence":["missing"]}],"prerequisites":[]}
    assert validate_lesson_plan(plan,knowledge)["passed"] is False
