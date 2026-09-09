import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from difficulty import calibrate_difficulty
from distractors import validate_distractors
from items import assessment_item,validate_item
def test_m230():
 assert calibrate_difficulty("APPLY",2,1)=="MEDIUM"
 i=assessment_item("a","o","MCQ","q","A",choices=["A","B","C"])
 assert validate_item(i)["passed"]
 assert validate_distractors("A",["A","B","C"])["passed"]
