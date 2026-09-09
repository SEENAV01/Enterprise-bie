import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_delivery
def test_delivery():
    r=compile_delivery("c","Course","1.0",
      [{"artifact_id":"v","path":"v.mp4","media_type":"video/mp4"}],
      [{"entity_id":"s","entity_type":"scene","source_refs":["book:p1"]}],
      [{"asset_id":"a","license":"CC-BY"}],"b1","r1","e1")
    assert r["quality_gate"]["valid"]
def test_license_gate():
    r=compile_delivery("c","Course","1.0",[],[{"entity_id":"s","entity_type":"scene"}],
      [{"asset_id":"a"}],"b1","r1","e1")
    assert not r["quality_gate"]["valid"]
