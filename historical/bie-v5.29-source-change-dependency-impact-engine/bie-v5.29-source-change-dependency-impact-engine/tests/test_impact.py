import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_impact_plan

def test_impact():
 nodes=["a","b","c","d"]; edges=[["a","b"],["b","c"],["a","d"]]
 r=compile_impact_plan(nodes,edges,["a"])
 assert set(r["impact"]["affected"])=={"b","c","d"}
 assert len(r["regeneration_plan"])==3

def test_block():
 r=compile_impact_plan(["a","b"],[["a","b"]],["a"],"DELETE")
 assert not r["quality_gate"]["valid"]
 assert r["regeneration_plan"]==[]
