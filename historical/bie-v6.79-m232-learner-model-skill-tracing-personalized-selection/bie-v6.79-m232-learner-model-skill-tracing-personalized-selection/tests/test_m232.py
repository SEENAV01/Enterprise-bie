import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from learner import learner,validate_learner
from skill_state import skill_state,update_skill
from selection import select_lessons
def test_m232():
 l=learner("x"); assert validate_learner(l)
 s=update_skill(skill_state("a",0,0),1); assert s["mastery"]==1
 ls=[{"lesson_id":"weak","skill_ids":["a"]},{"lesson_id":"strong","skill_ids":["b"]}]
 assert select_lessons(ls,{"a":0.1,"b":0.9},1)[0]["lesson_id"]=="weak"
