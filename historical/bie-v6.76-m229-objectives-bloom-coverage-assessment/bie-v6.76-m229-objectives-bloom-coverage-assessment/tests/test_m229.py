import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from bloom import assign_bloom
from lesson_plan import generate_lesson_plan,validate_plan
def test_m229():
 assert assign_bloom(["calculate"])=="APPLY"
 p=generate_lesson_plan("l1",[{"concept_id":"c1","title":"charge"}],["explain"])
 assert p["coverage"]["coverage"]==1
 assert validate_plan(p)["passed"]
