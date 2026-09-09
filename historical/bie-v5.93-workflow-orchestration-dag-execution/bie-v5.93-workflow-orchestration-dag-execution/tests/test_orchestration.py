import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from dag import dag,dependencies,ready_nodes
from scheduler import batches
from retry import retry_policy,can_retry,backoff
from checkpoint import checkpoint,latest
from control import control_request,apply_control

def test_dag():
 g=dag("w",["a","b","c"],
       [{"from":"a","to":"c"},{"from":"b","to":"c"}])
 assert dependencies(g,"c")==["a","b"]
 assert ready_nodes(g,["a","b"])==["c"]

def test_batches():
 assert batches(["a","b","c"],2)==[["a","b"],["c"]]

def test_retry():
 p=retry_policy(3,2,2)
 assert can_retry(1,p)
 assert backoff(2,p)==4

def test_checkpoint():
 xs=[checkpoint("a",1,"x"),checkpoint("a",2,"y")]
 assert latest(xs)["sequence"]==2

def test_control():
 e={"status":"RUNNING","cancelled":False}
 assert apply_control(e,control_request("w","PAUSE"))["status"]=="PAUSED"
