"""Seeded crash/lease-expiry controls; independent real-process smoke also required."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
import test_pr_reasoning_producer as f


class RecoveryTests(unittest.TestCase):
    setUp=f.DurableTests.setUp
    tearDown=f.DurableTests.tearDown
    complete=f.DurableTests.complete

    def crash(self,phase,steps):
        class Crash(BaseException):pass
        def fault(p):
            if p==phase:raise Crash()
        for _ in range(steps-1):self.port.work_once(self.p,self.run)
        with self.assertRaises(Crash):self.port.work_once(self.p,self.run,fault=fault)

    def repair(self):
        with self.port.native(self.p,self.run,"read") as n:
            with n.leases.db:n.leases.db.execute("UPDATE director_leases SET expires_at=0 WHERE state='ACTIVE'")
        self.port.recover(self.p,self.run)
        self.assertTrue(self.complete()["slice_complete"])

    def test_pr_cas_publication(self):
        self.crash("after_PREREQUISITE_prerequisite.graph_cas",4);self.repair()
    def test_pr_terminal_before_ack(self):
        self.crash("after_PREREQUISITE_terminal",4);self.repair()
    def test_reasoning_cas_publication(self):
        self.crash("after_REASONING_reasoning.decision_set_cas",5);self.repair()
    def test_reasoning_terminal_before_ack(self):
        self.crash("after_REASONING_terminal",5);self.repair()
    def test_pr_before_next_admission(self):
        self.crash("before_next_admission",4);self.assertTrue(self.complete()["slice_complete"])
    def test_knowledge_before_pr_admission(self):
        self.crash("before_next_admission",3);self.assertTrue(self.complete()["slice_complete"])
    def test_active_lease_not_recovered(self):
        self.crash("after_PREREQUISITE_cas",4)
        with self.assertRaises(Exception):self.port.recover(self.p,self.run)
    def test_stale_writer_rejected(self):
        with self.port.native(self.p,self.run,"read") as n:
            n.active_lease=n.leases.acquire("expired","intent",n.owner,now=0,ttl_seconds=1)
            with self.assertRaises(Exception):n.put(self.run,"PREREQUISITE","bad",{"test":True})
    def test_failed_attempt_history_retained(self):
        self.crash("after_REASONING_cas",5);self.repair()
        with self.port.native(self.p,self.run,"read") as n:
            a=n.persistence.load_run_state(self.run)["stages"]["REASONING"]["attempts"]
            self.assertEqual([x["state"] for x in a],["FAILED","SUCCEEDED"])
    def extension_crash(self,target):
        old=f.KnowledgeProducerControlPlane(self.operator,enabled_profiles={f.OLD_PROFILE})
        run=old.admit(self.p,self.source["source_id"],"legacy")["run_id"]
        for _ in range(3):old.work_once(self.p,run)
        class Crash(BaseException):pass
        def fault(phase):
            if phase==target:raise Crash()
        with self.assertRaises(Crash):
            with self.port.native(self.p,run,"create",fault=fault) as n:n.continue_completed(run,self.p.tenant)
        self.port.continue_completed(self.p,run)
        for _ in range(2):r=self.port.work_once(self.p,run)
        self.assertTrue(r["slice_complete"])
    def test_continuation_cas_before_stage_admission(self):self.extension_crash("after_continuation_publication")
    def test_continuation_stages_before_idempotency_complete(self):self.extension_crash("after_continuation_stage_admission")


if __name__=="__main__":unittest.main()
