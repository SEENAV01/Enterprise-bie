import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from templates import register_template,render_template
from budget import fit_token_budget
from output import validate_structured_output
def test_m275():
 s={}; t=register_template(s,"t","1","Hi {x}",["x"])
 assert render_template(t,{"x":"BIE"})=="Hi BIE"
 assert fit_token_budget(["a","b","c"],2)["used"]<=2
 assert validate_structured_output({"x":1},["x"])["valid"]
