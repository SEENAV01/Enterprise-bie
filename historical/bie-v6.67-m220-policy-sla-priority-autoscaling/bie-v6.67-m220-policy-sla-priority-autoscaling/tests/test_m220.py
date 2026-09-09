import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from policy import policy,validate
from slo import slo,compliance
from adaptive_scaling import scaling_decision
from deadline import deadline_state
def test_m220():
 p=policy("x","HIGH",100,True); assert validate(p)
 s=slo("x",.9); assert compliance(.95,s["target"])["compliant"]
 assert scaling_decision(2,3,1,2)["action"]=="SCALE_OUT"
 assert deadline_state({"deadline_seconds":100},90)=="AT_RISK"
