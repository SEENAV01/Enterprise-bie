"""Deterministic persisted crash-point/fence controls; not live-provider proof."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
import test_di_knowledge_producer as fixtures


class RecoveryTests(unittest.TestCase):
    setUp=fixtures.DurableTests.setUp
    tearDown=fixtures.DurableTests.tearDown
    complete=fixtures.DurableTests.complete

    def crash(self, target, steps):
        class Crash(BaseException):pass
        def fault(phase):
            if phase==target:raise Crash()
        for _ in range(steps-1):self.port.work_once(self.p,self.run)
        with self.assertRaises(Crash):self.port.work_once(self.p,self.run,fault=fault)

    def expire_interrupted_fixture_lease(self):
        # Seeded clock-expiry control, not a sleep or claimed real-time expiry.
        with self.port.native(self.p,self.run,"read") as native:
            with native.leases.db:
                native.leases.db.execute("UPDATE director_leases SET expires_at=0 WHERE state='ACTIVE'")

    def repair(self):
        self.expire_interrupted_fixture_lease()
        self.port.recover(self.p,self.run)
        self.assertTrue(self.complete()["slice_complete"])

    def test_document_cas_before_commit(self):
        self.crash("after_DOCUMENT_INTELLIGENCE_cas",2);self.repair()
    def test_knowledge_cas_before_commit(self):
        self.crash("after_KNOWLEDGE_knowledge.graph_cas",3)
        # Prove genuine graph bytes were published, not merely candidate bytes.
        with self.port.native(self.p,self.run,"read") as native:
            from bie.productization.candidates import produce
            from bie.productization.contracts import canonical,sha,profile_config
            from bie.infrastructure.artifact_store import BlobRef
            state=native.persistence.load_run_state(self.run)
            ref=state["stages"]["DOCUMENT_INTELLIGENCE"]["attempts"][-1]["output_artifact_refs"][0]
            graph=produce(native.read(self.run,ref),profile_config())[1]
            raw=canonical(graph)
            self.assertEqual(native.cas.get_bytes(BlobRef("sha256",sha(raw),len(raw))),raw)
        self.repair()
    def test_candidate_cas_before_commit(self):
        self.crash("after_KNOWLEDGE_knowledge.candidates_cas",3);self.repair()
    def test_di_terminal_before_ack(self):
        self.crash("after_DOCUMENT_INTELLIGENCE_terminal",2);self.repair()
    def test_knowledge_terminal_before_ack(self):
        self.crash("after_KNOWLEDGE_terminal",3);self.repair()
    def test_di_ack_before_next_admission(self):
        self.crash("before_next_admission",2);self.assertTrue(self.complete()["slice_complete"])
    def test_active_worker_cannot_be_recovered(self):
        self.crash("after_DOCUMENT_INTELLIGENCE_cas",2)
        with self.assertRaises(Exception):self.port.recover(self.p,self.run)
    def test_interrupted_attempt_preserved(self):
        self.crash("after_DOCUMENT_INTELLIGENCE_cas",2);self.repair()
        with self.port.native(self.p,self.run,"read") as n:
            attempts=n.persistence.load_run_state(self.run)["stages"]["DOCUMENT_INTELLIGENCE"]["attempts"]
            self.assertEqual([a["state"] for a in attempts],["FAILED","SUCCEEDED"])
    def test_stale_writer_cannot_publish(self):
        with self.port.native(self.p,self.run,"read") as n:
            n.active_lease=n.leases.acquire("expired","fingerprint",n.owner,now=0,ttl_seconds=1)
            with self.assertRaises(Exception):n.put(self.run,"SOURCE","bad",{"test":True})
    def test_missing_queue_admission_repaired(self):
        self.crash("before_next_admission",1)
        self.assertTrue(self.complete()["slice_complete"])
    def test_replay_after_source_admission_crash(self):
        from bie.productization.durable_slice import run_identity
        run=run_identity(self.p.tenant,"admission-crash")
        class Crash(BaseException):pass
        def fault(phase):
            if phase=="after_source_admission":raise Crash()
        source=dict(source_id=self.source["source_id"],sha256=self.source["sha256"],
            size_bytes=self.source["byte_length"],media_type="application/pdf",tenant=self.p.tenant,
            privacy="PRIVATE_LOCAL_CAS",rights="LOCAL_PROCESSING_ONLY")
        with self.assertRaises(Crash):
            with self.port.native(self.p,run,"create",fault=fault) as n:n.admit(source,self.p.tenant,"admission-crash")
        self.assertEqual(self.port.admit(self.p,self.source["source_id"],"admission-crash")["run_id"],run)


if __name__=="__main__":unittest.main()
