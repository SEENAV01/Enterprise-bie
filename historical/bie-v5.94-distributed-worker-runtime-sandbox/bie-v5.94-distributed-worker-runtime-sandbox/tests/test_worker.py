import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from worker import worker,register
from capability import requirement,satisfies,resource_satisfies
from dispatch import eligible_workers
from sandbox import sandbox,validate
from heartbeat import heartbeat,healthy
from result import task_result,successful

def test_worker_match():
 w=register(worker("w",["GPU"],{"cpu":4,"memory_mb":8192}))
 assert satisfies(w,[requirement("GPU")])
 assert resource_satisfies(w,{"cpu":2})
 assert eligible_workers([w],[requirement("GPU")],{"cpu":4})

def test_sandbox():
 assert validate(sandbox("s",network="DENY"))

def test_health():
 h=heartbeat("w",10,"READY")
 assert healthy(h["observed_at"],11,5)

def test_result():
 assert successful(task_result("t","w","SUCCEEDED"))
