import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))

from structured_content import detect_table_from_lines, detect_equation, link_captions, reading_order

def test_table_detection_is_conservative():
    result = detect_table_from_lines([
        {"text":"Quantity   Symbol"},
        {"text":"Charge     q"},
        {"text":"Mass       m"},
    ])
    assert result["kind"] == "TABLE"
    assert len(result["rows"]) == 3

def test_equation_candidate():
    result = detect_equation("F = ma")
    assert result["kind"] == "EQUATION_CANDIDATE"

def test_caption_linking():
    blocks = [
        {"block_id":"f1","kind":"FIGURE"},
        {"block_id":"c1","kind":"PARAGRAPH","text":"Figure 1. Electric field"},
    ]
    links = link_captions(blocks)
    assert links[0]["linked"] is True
    assert links[0]["target_block"] == "f1"

def test_bbox_reading_order():
    blocks = [
        {"block_id":"right","bbox":[500,100,600,150]},
        {"block_id":"left","bbox":[100,100,200,150]},
        {"block_id":"lower","bbox":[100,300,200,350]},
    ]
    assert [b["block_id"] for b in reading_order(blocks)] == ["left","right","lower"]
