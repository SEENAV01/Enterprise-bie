import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_governance

def manifest():
 return {"artifact_refs":["a"],"source_pins":["s"],
 "model_pins":["m"],"tool_pins":["t"],"policy_pins":["p"],
 "environment":{"runtime":"x"}}

def test_reproducible():
 r=compile_governance(manifest())
 assert r["reproducibility"]["reproducible"]
 assert r["quality_gate"]["valid"]

def test_missing_environment():
 m=manifest(); del m["environment"]
 r=compile_governance(m)
 assert not r["quality_gate"]["valid"]
