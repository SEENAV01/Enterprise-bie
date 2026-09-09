import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from examples import worked_example,validate_example
from scaffolding import scaffold_steps
from hints import escalate_hint
from reveal import reveal_policy
def test_m247():
 e=worked_example("e","c","p",["s1","s2"],"a")
 assert validate_example(e)["passed"]
 assert scaffold_steps(e,0)["next_step"]=="s1"
 assert escalate_hint("CONCEPT")=="STRATEGY"
 assert not reveal_policy(False,False,"STEP")["allowed"] or reveal_policy(False,False,"STEP")["level"]=="STEP"
