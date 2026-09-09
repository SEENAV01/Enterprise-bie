import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from lock import lock_record,valid_owner
from lease import lease,active
from fencing import next_fencing_token,reject_stale
from election import election_candidate,elect
from coordination import coordination_state,compare_and_set

def test_lock_lease():
 l=lock_record("l","r","a",4,10)
 assert valid_owner(l,"a",5)
 assert active(lease("x","a",1,10),5)

def test_fencing():
 assert next_fencing_token(41)==42
 assert reject_stale(41,42)

def test_election():
 c=[election_candidate("a",2,1),
    election_candidate("b",2,2)]
 assert elect(c)["node_id"]=="b"

def test_cas():
 c=coordination_state("x",1,3)
 assert compare_and_set(c,3,2)["version"]==4
