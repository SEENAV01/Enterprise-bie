import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from equation import create_equation,apply_equation_step,validate_equation_step
from diagram import create_diagram,validate_diagram
from visual_validation import validate_visual_step
def test_m249():
 e=create_equation("e","x=y")
 s=apply_equation_step(e,"sub","x=2")
 assert validate_equation_step(s,"x=2")["valid"]
 assert validate_diagram(create_diagram("d",[]))["passed"]
 assert validate_visual_step({"a":1},{"a":1})["valid"]
