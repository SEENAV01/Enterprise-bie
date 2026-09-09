import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from states import valid_transition
from approval import request_approval,decide
from gates import deployment_gate
def test_m265():
 assert valid_transition("CREATED","QUEUED")
 assert not valid_transition("CREATED","RELEASED")
 r=request_approval("x"); assert decide(r,"APPROVE","a")["request"]["decision"]=="APPROVE"
 assert deployment_gate(True,True,True,True)["release"]
