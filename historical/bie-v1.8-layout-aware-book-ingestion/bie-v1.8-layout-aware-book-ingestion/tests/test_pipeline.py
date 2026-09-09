import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from pipeline import run

def test_layout_pipeline(tmp_path):
    src=Path(__file__).parents[1]/"examples/document-ir.json"
    out=tmp_path/"out.json"
    r=run(src,out)
    assert r["heading_tree"]
    assert len(r["assets"])==3
    assert r["chapter_units"]
