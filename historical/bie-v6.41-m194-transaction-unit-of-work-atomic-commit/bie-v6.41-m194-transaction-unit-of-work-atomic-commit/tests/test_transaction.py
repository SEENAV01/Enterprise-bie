import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from transaction import transaction,open_tx
from unit_of_work import unit_of_work,add_operation
from read_write_set import read_write_set,overlaps
from prepare import prepare,prepared
from commit import commit,committed
from rollback import rollback,rolled_back
from conflict import conflict,detected
from idempotency import idempotency,matches
from savepoint import savepoint,valid

def test_transaction_uow():
 t=transaction("t","SERIALIZABLE")
 assert open_tx(t)
 u=add_operation(unit_of_work("u","t"),{"operation":"WRITE"})
 assert len(u["operations"])==1

def test_prepare_commit_rollback_conflict():
 rw=read_write_set(["a"],["a"])
 assert overlaps(rw,rw)
 assert prepared(prepare("t",rw))
 assert committed(commit("t"))
 assert rolled_back(rollback("t"))
 assert detected(conflict("t","x","a"))

def test_idempotency_savepoint():
 assert matches(idempotency("k","h"),"k","h")
 assert valid(savepoint("t","s",0))
