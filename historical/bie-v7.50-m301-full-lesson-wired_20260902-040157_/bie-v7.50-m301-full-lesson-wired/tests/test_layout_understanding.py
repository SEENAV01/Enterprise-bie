import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))

from understanding_adapter import classify_block, build_hierarchy

def test_block_classification():
    assert classify_block("Chapter 1: Charge") == "HEADING"
    assert classify_block("2.1 Electric field") == "HEADING"
    assert classify_block("Electric charge is a property of matter.") == "PARAGRAPH"

def test_hierarchy():
    ir = {"pages":[{"page":1,"blocks":[
        {"block_id":"h1","kind":"HEADING","text":"Chapter 1: Charge"},
        {"block_id":"p1","kind":"PARAGRAPH","text":"Charge is a property."},
        {"block_id":"h2","kind":"HEADING","text":"2.1 Types"},
        {"block_id":"p2","kind":"PARAGRAPH","text":"There are two signs."}
    ]}]}
    sections = build_hierarchy(ir)
    assert len(sections) == 2
    assert sections[0]["blocks"] == ["p1"]
    assert sections[1]["blocks"] == ["p2"]
