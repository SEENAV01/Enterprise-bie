import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from mastery import mastery_score,mastery_level
from readiness import prerequisite_readiness
from difficulty import choose_difficulty
def test_m244():
 s=mastery_score({"assessment":1,"practice":1,"completion":1,"confidence":1})
 assert s==1 and mastery_level(s)=="MASTERED"
 assert prerequisite_readiness("b",["a"],{"a":.8})["ready"]
 assert choose_difficulty(.9)["level"]=="ADVANCED"
