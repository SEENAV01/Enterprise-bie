import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from sources import source,validate_source
from evidence import evidence,validate_evidence
from claims import grounded_claim,verify_claim
def test_m239():
 s=source("s","uri"); assert validate_source(s)["passed"]
 e=evidence("e","s","fact"); assert validate_evidence(e,{"s"})["passed"]
 c=grounded_claim("c","fact",["e"],.9); assert verify_claim(c,{"e":e})["passed"]
