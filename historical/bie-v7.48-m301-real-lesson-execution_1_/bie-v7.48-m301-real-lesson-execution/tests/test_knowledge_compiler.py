import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))

from knowledge_compiler import compile_knowledge, validate_grounding

def test_claims_are_grounded():
    ir = {
        "source_uri":"book.pdf",
        "pages":[{"page":4,"blocks":[
            {"block_id":"p4b1","kind":"PARAGRAPH",
             "text":"Electric charge is a property of matter."}
        ]]
    }
    k = compile_knowledge(ir)
    assert len(k["claims"]) == 1
    assert k["claims"][0]["source_block_id"] == "p4b1"
    assert validate_grounding(k)["passed"] is True

def test_unresolved_claim_fails_validation():
    k = {
        "evidence_index":{"p1":{}},
        "claims":[{"claim_id":"c1","source_block_id":"missing","text":"x"}],
        "relations":[]
    }
    assert validate_grounding(k)["passed"] is False

def test_relations_are_not_overstated():
    ir = {
        "source_uri":"book.pdf",
        "pages":[{"page":1,"blocks":[
            {"block_id":"b1","kind":"PARAGRAPH",
             "text":"Charge and matter are discussed together."}
        ]]
    }
    k = compile_knowledge(ir)
    assert all(r["predicate"] == "co_occurs_in_claim" for r in k["relations"])
