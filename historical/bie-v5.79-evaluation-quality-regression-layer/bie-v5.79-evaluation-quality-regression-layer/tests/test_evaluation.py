import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from evaluate import evaluate_case,evaluate_suite
from regression import regression
from gates import promotion_gate

def test_case_pass():
 r=evaluate_case("a",{"correctness":1.0},
                 {"correctness":1.0},.9)
 assert r["passed"]

def test_regression():
 r=regression(.95,.80,.01,.01)
 assert r["regression"]

def test_gate():
 assert promotion_gate({"passed":True})["allowed"]
