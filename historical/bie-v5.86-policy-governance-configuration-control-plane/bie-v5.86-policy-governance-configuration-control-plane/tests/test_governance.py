import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from overlay import effective_policy
from simulation import simulate,diff_decisions
from change_control import change_request,approve
from flags import feature_flag,enabled

def test_overlay():
 assert effective_policy({"a":1},{"b":2})=={"a":1,"b":2}

def test_simulation_diff():
 a=simulate({"policy_id":"p","version":"1","allow":True},[{}])
 b=simulate({"policy_id":"p","version":"2","allow":False},[{}])
 assert diff_decisions(a,b)

def test_change():
 r=change_request("r","p","1","2","u","reason")
 assert approve(r,"admin")["status"]=="APPROVED"

def test_flag():
 assert enabled(feature_flag("x",True,["prod"]),"prod")
