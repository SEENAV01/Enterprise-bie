"""Seeded interruption controls; immutable failed attempts retained."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
import test_math_producer as f


class MathRecoveryTests(unittest.TestCase):
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

    def test_candidate_publish_interruption(self):self.crash("after_MATH_math.evidence.candidates_cas",5);self.repair()
    def test_math_cas_interruption(self):self.crash("after_MATH_math.evidence_cas",5);self.repair()
    def test_math_terminal_before_ack(self):self.crash("after_MATH_terminal",5);self.repair()
    def test_math_before_reasoning_admission(self):self.crash("before_next_admission",5);self.assertTrue(self.complete()["slice_complete"])
    def test_pr_before_math_admission(self):self.crash("before_next_admission",4);self.assertTrue(self.complete()["slice_complete"])
    def test_reasoning_math_consumer_cas(self):self.crash("after_REASONING_reasoning.decision_set_cas",6);self.repair()
    def test_reasoning_terminal_before_ack(self):self.crash("after_REASONING_terminal",6);self.repair()
    def test_active_lease_cannot_recover(self):
        self.crash("after_MATH_cas",5)
        with self.assertRaises(Exception):self.port.recover(self.p,self.run)
    def test_stale_math_writer(self):
        with self.port.native(self.p,self.run,"read") as n:
            n.active_lease=n.leases.acquire("expired","intent",n.owner,now=0,ttl_seconds=1)
            with self.assertRaises(Exception):n.put(self.run,"MATH","math.evidence",{})
    def test_failed_attempt_retained(self):
        self.crash("after_MATH_cas",5);self.repair()
        with self.port.native(self.p,self.run,"read") as n:
            rows=n.persistence.load_run_state(self.run)["stages"]["MATH"]["attempts"]
            self.assertEqual([a["state"] for a in rows],["FAILED","SUCCEEDED"])
            self.assertTrue(rows[0]["evidence_refs"])
    def test_terminal_tamper_not_acked(self):
        self.crash("after_MATH_terminal",5)
        with self.port.native(self.p,self.run,"read") as n:
            ref=n.persistence.load_run_state(self.run)["stages"]["MATH"]["attempts"][-1]["output_artifact_refs"][0]
            record=n.record(self.run,ref);n.cas._path(record.blob_digest).write_bytes(b"tampered")
            with n.leases.db:n.leases.db.execute("UPDATE director_leases SET expires_at=0 WHERE state='ACTIVE'")
        with self.assertRaises(Exception):self.port.recover(self.p,self.run)
    def test_completed_identity_recovery(self):
        expected=self.complete();self.assertEqual(self.port.recover(self.p,self.run),expected)
    def test_semantic_forgery_recovery_not_acked(self):
        import json
        self.crash("after_MATH_terminal",5)
        with self.port.native(self.p,self.run,"read") as n:
            current=n.persistence.load_run_state(self.run)["stages"]["MATH"]["attempts"][-1]
            old=current["output_artifact_refs"][0];record=n.record(self.run,old)
            forged=n.read(self.run,old);forged["applicability"]="NOT_REQUIRED"
            new=n.put(self.run,"MATH","math.evidence",forged,record.parent_artifact_ids)
            with n.persistence._conn() as db:db.execute("UPDATE attempts SET output_refs_json=? WHERE stage_id='MATH' AND attempt=1",(json.dumps([new]),))
            with n.leases.db:n.leases.db.execute("UPDATE director_leases SET expires_at=0 WHERE state='ACTIVE'")
        with self.assertRaises(Exception):self.port.recover(self.p,self.run)
        with self.port.native(self.p,self.run,"read") as n:
            self.assertEqual(n.queue.get(n.task_id(self.run,"MATH",1)).state,"DELIVERED")


if __name__=="__main__":unittest.main()
