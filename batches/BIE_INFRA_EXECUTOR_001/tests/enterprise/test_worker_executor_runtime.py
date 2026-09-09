import unittest
from enterprise.worker_executor_runtime import *
from enterprise.worker_scheduler import *
from enterprise.leases import *

class FakeClock:
    def __init__(self):self.t=100.0
    def __call__(self):return self.t
    def advance(self,x):self.t+=x

def env(clock=None):
    scheduler=CapabilityScheduler([
        WorkerCapabilities("w1",{"python","sandbox"},8,16,2)
    ])
    leases=LeaseManager(clock)
    guard=WorkerOwnershipGuard(leases)
    runtime=WorkerExecutorRuntime(scheduler,leases,guard,LeaseKey,10)
    req=StageResourceRequirement("REASONING",{"python"},1,1,1)
    task=WorkerTask("r1","REASONING",1,["src"])
    return scheduler,leases,guard,runtime,req,task

class ExecutorRuntimeTests(unittest.TestCase):
    def test_successful_execution_and_cleanup(self):
        s,l,g,r,req,task=env()
        committed=[]
        result=r.execute(task,req,
            lambda ctx: WorkerExecutionResult(["out"],["ev"]),
            lambda ctx,res: committed.append((ctx.worker_id,ctx.fencing_token,res.output_artifact_refs)),
            "RE")
        self.assertEqual(result.output_artifact_refs,["out"])
        self.assertEqual(committed[0][0],"w1")
        self.assertEqual(s.loads["w1"].active_slots,0)

    def test_heartbeat_renews_lease(self):
        clock=FakeClock(); s,l,g,r,req,task=env(clock)
        seen=[]
        def ex(ctx):
            first=l.active_lease(LeaseKey("r1","REASONING",1)).expires_at
            clock.advance(5); ctx.heartbeat()
            second=l.active_lease(LeaseKey("r1","REASONING",1)).expires_at
            seen.extend([first,second])
            return WorkerExecutionResult(["out"],["ev"])
        r.execute(task,req,ex,lambda c,res:None,"RE")
        self.assertGreater(seen[1],seen[0])

    def test_expired_lease_blocks_commit(self):
        clock=FakeClock(); s,l,g,r,req,task=env(clock)
        def ex(ctx):
            clock.advance(11)
            return WorkerExecutionResult(["out"],["ev"])
        with self.assertRaises(Exception):
            r.execute(task,req,ex,lambda c,res:None,"RE")
        self.assertEqual(s.loads["w1"].active_slots,0)

    def test_execution_exception_releases_capacity(self):
        s,l,g,r,req,task=env()
        def ex(ctx): raise RuntimeError("boom")
        with self.assertRaises(ExecutorRuntimeError):
            r.execute(task,req,ex,lambda c,res:None,"RE")
        self.assertEqual(s.loads["w1"].active_slots,0)

    def test_result_requires_evidence(self):
        s,l,g,r,req,task=env()
        with self.assertRaises(Exception):
            r.execute(task,req,lambda c:WorkerExecutionResult(["out"],[]),lambda c,res:None,"RE")

    def test_result_requires_output(self):
        s,l,g,r,req,task=env()
        with self.assertRaises(Exception):
            r.execute(task,req,lambda c:WorkerExecutionResult([],["ev"]),lambda c,res:None,"RE")

    def test_commit_scope_uses_exact_attempt(self):
        s,l,g,r,req,task=env()
        seen=[]
        def commit(ctx,res): seen.append(ctx.task.attempt)
        r.execute(task,req,lambda c:WorkerExecutionResult(["out"],["ev"]),commit,"RE")
        self.assertEqual(seen,[1])

    def test_scheduler_failure_means_no_execution(self):
        scheduler=CapabilityScheduler([WorkerCapabilities("w1",{"node"},4,8,1)])
        leases=LeaseManager(); guard=WorkerOwnershipGuard(leases)
        runtime=WorkerExecutorRuntime(scheduler,leases,guard,LeaseKey,10)
        req=StageResourceRequirement("R",{"python"})
        task=WorkerTask("r","R",1,[])
        called=[]
        with self.assertRaises(Exception):
            runtime.execute(task,req,lambda c:(called.append(1) or WorkerExecutionResult(["o"],["e"])),lambda c,r:None,"RE")
        self.assertEqual(called,[])

    def test_lease_acquisition_failure_releases_capacity(self):
        s,l,g,r,req,task=env()
        # Pre-lease same stage attempt so runtime cannot acquire.
        l.acquire(LeaseKey("r1","REASONING",1),"other",10)
        with self.assertRaises(Exception):
            r.execute(task,req,lambda c:WorkerExecutionResult(["out"],["ev"]),lambda c,res:None,"RE")
        self.assertEqual(s.loads["w1"].active_slots,0)

    def test_stale_worker_takeover_is_fenced(self):
        clock=FakeClock()
        l=LeaseManager(clock)
        key=LeaseKey("r","S",1)
        old=l.acquire(key,"w1",5)
        clock.advance(6)
        new=l.acquire(key,"w2",5)
        with self.assertRaises(LeaseError): l.commit_guard(old)
        l.commit_guard(new)

if __name__=="__main__":unittest.main()
