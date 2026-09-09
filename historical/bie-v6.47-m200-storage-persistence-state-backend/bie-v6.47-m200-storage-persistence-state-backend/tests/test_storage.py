import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from key_value import record,same_key
from blob import blob,has_checksum
from collection import collection,active
from namespace import namespace
from versioning import version,matches
from conditional import condition,evaluate
from transaction import transaction,add
from snapshot import snapshot,available
from consistency import consistency,strong

def test_records_and_collections():
 r=record("n","k",1)
 assert same_key(r,r)
 assert has_checksum(blob("b","ref",checksum="sha"))
 assert active(collection("c","n"))
 assert namespace("n","name")["status"]=="ACTIVE"

def test_version_condition_transaction():
 assert matches(version(3),3)
 assert evaluate(condition("x","EQ",1),1)
 assert len(add(transaction("t"),{"op":"PUT"})["operations"])==1

def test_snapshot_consistency():
 assert available(snapshot("s","n",3))
 assert strong(consistency("STRONG"))
