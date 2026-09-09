import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from factuality import claim,validate_claim
from definitions import definition,verify_definition
from formulas import formula,verify_formula
def test_m238():
 assert validate_claim(claim("c","fact",["s"]),True)["passed"]
 assert verify_definition(definition("x","x is a thing",["thing"]))["passed"]
 assert verify_formula(formula("f","F=q*E",["F","q","E"]))["passed"]
