import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from entity import entity,has_field
from repository import repository,contract
from query import query,matches
from transaction import transaction,commit,rollback
from index import index,covers
from migration import migration,applied
from archive import archive_policy,archival_due
from storage_lifecycle import lifecycle,valid_transition
from consistency import consistency_contract,compatible

def test_entity_repository_query():
 e=entity("x",{"id":"string","v":"int"},True,True)
 assert has_field(e,"v")
 r=repository("r","x")
 assert contract(r)["entity"]=="x"
 q=query("x",{"status":"A"})
 assert matches({"status":"A"},q["filters"])

def test_transaction_index_migration():
 assert commit(transaction("t"))["status"]=="COMMITTED"
 assert rollback(transaction("t"))["status"]=="ROLLED_BACK"
 i=index("i","x",["tenant_id","status"])
 assert covers(i,["tenant_id"])
 assert applied(migration("m",1,2,[]))["status"]=="APPLIED"

def test_archive_lifecycle_consistency():
 a=archive_policy("x",10,20)
 assert archival_due(a,20)
 assert valid_transition("ACTIVE","ARCHIVED")
 assert not valid_transition("DELETED","ACTIVE")
 c=consistency_contract("x")
 assert compatible(c,{"STRONG"})
