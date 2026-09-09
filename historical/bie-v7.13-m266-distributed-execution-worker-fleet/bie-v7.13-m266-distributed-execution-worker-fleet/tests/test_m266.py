import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from workers import register_worker
from scheduler import match_worker
from leases import acquire_lease,expire_lease
from faults import recover_expired_job
from autoscale import desired_workers
def test_m266():
 w=register_worker("w",["render"],1)
 assert match_worker([w],"render")["worker_id"]=="w"
 l=expire_lease(acquire_lease("j","w","l",10))
 r=recover_expired_job({"job_id":"j","status":"RUNNING","attempt":0},l)
 assert r["requeue"] and r["job"]["attempt"]==1
 assert desired_workers(8,2)>1
