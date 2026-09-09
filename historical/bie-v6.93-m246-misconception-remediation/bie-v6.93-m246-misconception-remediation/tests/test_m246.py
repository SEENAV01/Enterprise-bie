import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from misconceptions import detect_misconception
from hints import generate_hint
from remediation import remediation_plan
from reassessment import reassessment_decision
def test_m246():
 r=detect_misconception([{"error":{"type":"UNIT_ERROR"}}])
 assert r[0]["type"]=="UNIT_ERROR"
 assert "unit" in generate_hint("UNIT_ERROR","X").lower()
 assert remediation_plan("X",["UNIT_ERROR"])[0]["reassessment_required"]
 assert reassessment_decision(.4,.8)["passed"]
