
import unittest
from enterprise.e2e_runtime import *

class E2ETests(unittest.TestCase):
    def task(self): return StageTask("t1","r1","REASONING",1,["src"],["python"])
    def test_success(self):
        rt=EnterpriseRuntime(); rt.submit(self.task())
        r=rt.consume_once("w1",["python"],lambda t:{"payload":{"ok":1},"evidence_refs":["ev1"]})
        self.assertEqual(r["outcome"],"ACKED"); self.assertEqual(rt.queue.state("t1"),"ACKED")
    def test_commit_before_ack(self):
        rt=EnterpriseRuntime(); rt.submit(self.task()); order=[]
        orig=rt.queue.ack
        def ack(*a,**k): order.append("ack"); return orig(*a,**k)
        rt.queue.ack=ack
        rt.consume_once("w1",["python"],lambda t:{"payload":{"ok":1},"evidence_refs":["ev"]},lambda *a: order.append("commit"))
        self.assertEqual(order,["commit","ack"])
    def test_commit_failure_retries(self):
        rt=EnterpriseRuntime(); rt.submit(self.task())
        r=rt.consume_once("w1",["python"],lambda t:{"payload":{"ok":1},"evidence_refs":["ev"]},lambda *a: (_ for _ in ()).throw(RuntimeError("db")))
        self.assertEqual(r["outcome"],"RETRY"); self.assertEqual(rt.queue.state("t1"),"READY")
    def test_missing_evidence_retries(self):
        rt=EnterpriseRuntime(); rt.submit(self.task())
        r=rt.consume_once("w1",["python"],lambda t:{"payload":{"ok":1},"evidence_refs":[]})
        self.assertEqual(r["outcome"],"RETRY")
    def test_capability_mismatch_idle(self):
        rt=EnterpriseRuntime(); rt.submit(self.task())
        self.assertEqual(rt.consume_once("w1",["gpu"],lambda t:{} )["outcome"],"IDLE")
    def test_duplicate_enqueue_idempotent(self):
        rt=EnterpriseRuntime(); t=self.task(); rt.submit(t); rt.submit(t)
        self.assertEqual(len(rt.queue._items),1)
    def test_conflicting_task_rejected(self):
        rt=EnterpriseRuntime(); rt.submit(self.task())
        with self.assertRaises(E2ERuntimeError):
            rt.submit(StageTask("t1","r2","REASONING",1,["src"],["python"]))
    def test_artifact_dedup(self):
        s=InMemoryArtifactStore()
        a=s.put("r","s",{"x":1},["e"]); b=s.put("r","s",{"x":1},["e"])
        self.assertEqual(a,b); self.assertEqual(len(s.records),1)
    def test_stage_attempt_preserved(self):
        rt=EnterpriseRuntime(); rt.submit(self.task())
        rt.consume_once("w",["python"],lambda t:{"payload":{"a":t.attempt},"evidence_refs":["e"]})
        self.assertEqual(rt.state.stage_states[("r1","REASONING")]["attempt"],1)
    def test_no_release_success_side_effect(self):
        rt=EnterpriseRuntime(); rt.submit(self.task())
        rt.consume_once("w",["python"],lambda t:{"payload":{"x":1},"evidence_refs":["e"]})
        self.assertFalse(any("RELEASE" in str(e) for e in rt.state.events))
if __name__=="__main__": unittest.main()
