import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from claims import claim,validate_claim
from math_check import check_equation
from physics_check import check_units
from multimodal_check import check_modalities
def test_m225():
    c=claim("x","F=ma","EQUATION"); assert validate_claim(c)
    assert check_equation(4,4)["passed"]
    assert check_units("N","N")["passed"]
    assert check_modalities({"narration","visual","captions"})["passed"]
