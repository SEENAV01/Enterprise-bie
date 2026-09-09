import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from lease import lease,valid
from fencing import fencing_token,permits
from mutex import mutex,acquirable
from leader import leadership,is_leader
from quorum import quorum,reached
from epoch import ownership_epoch,newer
from failure import failure_detector,suspected
from coordination import coordination_request,complete
from observability import coordination_event,metric

def test_lease_fencing_mutex():
 l=lease("r","w",100,2)
 assert valid(l,50)
 assert permits(fencing_token("r",2),2)
 assert acquirable(mutex("r"))

def test_leader_quorum_epoch_failure():
 g=leadership("g","w",3)
 assert is_leader(g,"w")
 assert reached(quorum(5),3)
 a=ownership_epoch("r",2,"a")
 b=ownership_epoch("r",3,"b")
 assert newer(b,a)
 assert suspected(failure_detector("n",10,5),15)

def test_request_observability():
 r=complete(coordination_request("x","r","RELEASE","w"))
 assert r["status"]=="COMPLETED"
 e=coordination_event("e","r","RELEASE","DONE","w",2,1.2)
 assert metric(e)["epoch"]==2
