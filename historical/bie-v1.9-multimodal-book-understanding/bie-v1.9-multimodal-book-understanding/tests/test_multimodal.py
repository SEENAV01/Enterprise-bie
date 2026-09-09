import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from pipeline import run

def test_multimodal_payload(tmp_path):
    src=Path(__file__).parents[1]/"examples/document.json"
    out=tmp_path/"out.json"
    r=run(src,out)
    assert len(r["multimodal_payload"]["visual_assets"])==3
    assert any(x["role"]=="process_or_system_visual" for x in r["visual_learning_roles"])
