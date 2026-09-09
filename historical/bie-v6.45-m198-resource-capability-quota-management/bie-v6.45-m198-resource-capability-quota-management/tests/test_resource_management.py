import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from resource import resource,active
from capability import capability,available
from unit import capacity_unit,normalize
from quota import quota,within_limit
from budget import budget,sufficient
from reservation import reservation,activate
from allocation import allocation,allocated
from admission import admission,admitted
from utilization import utilization,saturated

def test_resource_capability_unit():
 assert active(resource("r","COMPUTE"))
 assert available(capability("c","r","CPU"))
 assert normalize(2,capacity_unit("core",2))==4

def test_quota_budget_reservation():
 assert within_limit(quota("q","s","r",10,burst=2),12)
 assert sufficient(budget("b","s","r",20),10,5)
 assert activate(reservation("x","s","r",2))["status"]=="ACTIVE"

def test_allocation_admission_utilization():
 assert allocated(allocation("a","x","r",2))
 assert admitted(admission("s","r",2,5))
 assert saturated(utilization("r",100,100))
