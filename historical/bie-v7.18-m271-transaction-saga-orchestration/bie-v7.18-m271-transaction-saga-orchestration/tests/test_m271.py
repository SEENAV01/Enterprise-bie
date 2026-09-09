import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from saga import create_saga
from transaction import begin,rollback
from effects import apply_once
from failure import failure_policy
def test_m271():
 s=create_saga("s",[{"id":"a","compensation":"undo"}]); assert s["status"]=="RUNNING"
 t=rollback(begin("t")); assert t["status"]=="ROLLED_BACK"
 store={}; assert apply_once(store,"k",1)["applied"]; assert apply_once(store,"k",1)["duplicate"]
 assert failure_policy("PARTIAL_COMMIT",1)["action"]=="COMPENSATE"
