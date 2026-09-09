import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))

from job import job,valid
from queue import JobQueue
from resources import resource_pool,allocate
from worker import worker,can_run
from retry import retry_policy,should_retry
from checkpoint import checkpoint,valid as checkpoint_valid
from failure import worker_failure,recovery_action
from aggregation import aggregate

def test_runtime_contracts():
    j=job("j","lesson",resources={"cpu":1,"memory":2})
    q=JobQueue(); q.enqueue(j); assert valid(q.dequeue())
    pool=resource_pool(4,8,0)
    assert allocate({"cpu":1,"memory":2},pool)["cpu"]==3
    w=worker("w",["cpu"])
    assert can_run(w,j)
    p=retry_policy(3)
    assert should_retry(j,"WORKER_LOST",p)
    cp=checkpoint("cp","j",1,"RENDERED")
    f=worker_failure("w","CRASH",["j"],True)
    assert checkpoint_valid(cp)
    assert recovery_action(f)=="REQUEUE_AFFECTED_JOBS"
    assert aggregate([{"status":"SUCCEEDED"}])["status"]=="SUCCEEDED"
