import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from dag import validate_dag,ready_nodes
from retry import retry_policy
from idempotency import accept_once
def test_m267():
 n=[{"id":"a"},{"id":"b"}]; e=[{"source":"a","target":"b"}]
 assert validate_dag(n,e)["valid"]
 assert ready_nodes(n,e,{"a"})==["b"]
 assert retry_policy(0)["retry"]
 s={}; assert accept_once(s,"k",1)["accepted"]; assert not accept_once(s,"k",2)["accepted"]
