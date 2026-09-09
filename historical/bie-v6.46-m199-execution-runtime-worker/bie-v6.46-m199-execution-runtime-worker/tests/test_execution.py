import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from worker import worker,ready
from runtime import runtime,available
from job import job,queued
from task import task,runnable
from attempt import attempt,running
from placement import placement,selected
from cancellation import cancellation,requested
from heartbeat import heartbeat,healthy
from health import worker_health
def test_worker_runtime_job_task():
 assert ready(worker("w"))
 assert available(runtime("r","container"))
 assert queued(job("j",{}))
 assert runnable(task("t","j",{}))
def test_attempt_placement_cancel():
 assert running(attempt("a","t"))
 assert selected(placement("t","w"))
 assert requested(cancellation("t"))
def test_heartbeat_health():
 assert healthy(heartbeat("w","now"))
 assert worker_health("w")["state"]=="HEALTHY"
