import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from participant import participant,active
from epoch import epoch,current
from lease import lease,held_by
from leader import leader_term,is_leader
from quorum import quorum,reached
from prepare import prepare,prepared
from accept import accept,accepted
from finalize import finalize,finalized
from membership import membership,contains

def test_participant_epoch_lease_leader():
 p=participant("n")
 assert active(p)
 assert current(epoch(2),2)
 assert held_by(lease("l","n",10),"n")
 assert is_leader(leader_term(2,"n","2"),"n")

def test_quorum_states():
 q=quorum(["a","b","c"])
 assert reached(q,["a","b"])
 assert prepared(prepare("c","a",1,"h"))
 assert accepted(accept("c","a",1,"h"))
 assert finalized(finalize("c",1,"h"))

def test_membership():
 assert contains(membership("e",["a","b"]),"b")
