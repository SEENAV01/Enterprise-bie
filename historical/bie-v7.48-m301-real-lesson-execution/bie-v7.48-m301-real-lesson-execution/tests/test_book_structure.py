import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))

from book_structure import compile_sections, flatten_sections, validate_structure

def test_nested_numbered_structure():
    ir={"pages":[{"page":1,"blocks":[
        {"block_id":"1","kind":"HEADING","text":"1 Introduction"},
        {"block_id":"1.1","kind":"HEADING","text":"1.1 Charge"},
        {"block_id":"p","kind":"PARAGRAPH","text":"Charge is a property."},
        {"block_id":"1.2","kind":"HEADING","text":"1.2 Interaction"},
    ]}]}
    tree=compile_sections(ir)
    assert tree[0]["title"]=="1 Introduction"
    assert tree[0]["children"][0]["title"]=="1.1 Charge"
    assert tree[0]["children"][0]["content_blocks"]==["p"]
    assert validate_structure(tree)["passed"] is True
    assert len(flatten_sections(tree))==3

def test_toc_like_heading_is_ignored():
    ir={"pages":[{"page":1,"blocks":[
        {"block_id":"toc","kind":"HEADING","text":"1 Introduction .... 3"},
        {"block_id":"h","kind":"HEADING","text":"1 Introduction"}
    ]}]}
    tree=compile_sections(ir)
    assert len(tree)==1
    assert tree[0]["section_id"]=="h"
