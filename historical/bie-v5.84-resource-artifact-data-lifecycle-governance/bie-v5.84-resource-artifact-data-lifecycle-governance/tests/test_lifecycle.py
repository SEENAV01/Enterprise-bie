import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from retention import retention_policy,retention_action
from holds import hold,deletion_blocked
from lineage import dependency_graph
from gc import deletion_decision

def test_retention():
 p=retention_policy("p",ttl_seconds=100)
 assert retention_action(101,p)=="DELETE"

def test_hold():
 h=hold("h","a","LEGAL","case")
 assert deletion_blocked("a",[h])

def test_dependency():
 g=dependency_graph([{"parent_id":"a","child_id":"b"}])
 assert "b" in g["a"]

def test_delete_block():
 assert deletion_decision("a",[],{"a":{"b"}})=="BLOCKED_BY_DEPENDENCY"
