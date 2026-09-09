import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from gates import quality_gate,evaluate_gate

def test_gate_pass():
 r=[{"category":"SEMANTIC","status":"PASS"}]
 g=quality_gate("g",["SEMANTIC"])
 assert evaluate_gate(r,g)["passed"]

def test_missing_check_fails():
 r=[]
 g=quality_gate("g",["SEMANTIC"])
 assert not evaluate_gate(r,g)["passed"]
