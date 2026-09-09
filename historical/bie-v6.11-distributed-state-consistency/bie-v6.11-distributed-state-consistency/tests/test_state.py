import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from entity import entity
from concurrency import update_if_version
from sequence import sequence,accept
from version_vector import version_vector,increment,dominates,concurrent
from transaction import transaction,commit
from idempotent_transition import transition
from consistency import consistency_contract
from conflict import conflict,resolve
from reconciliation import reconciliation,mark

def test_versioned_update():
 e=entity("e","X",version=2)
 assert update_if_version(e,2,{"x":1})["status"]=="UPDATED"
 assert update_if_version(e,1,{"x":2})["status"]=="CONFLICT"

def test_sequence_vector():
 s=sequence("e",0)
 assert accept(s,0)
 assert not accept(s,0)
 a=increment(version_vector({"a":1}),"a")
 assert dominates(a,{"a":1})
 assert concurrent({"a":2},{"b":2})

def test_transaction_transition():
 assert commit(transaction("t",[]))["status"]=="COMMITTED"
 state={"x":1}
 first=transition(state,"op","SET",{"x":2})
 second=transition(first["state"],"op","SET",{"x":3})
 assert first["status"]=="APPLIED"
 assert second["status"]=="ALREADY_APPLIED"

def test_consistency_conflict_reconcile():
 assert consistency_contract("x","CAUSAL")["level"]=="CAUSAL"
 c=resolve(conflict("e",1,2,{},{}),{"x":1},"MANUAL")
 assert c["status"]=="RESOLVED"
 assert mark(reconciliation("e",{}, {},0),"CONVERGED")["status"]=="CONVERGED"
