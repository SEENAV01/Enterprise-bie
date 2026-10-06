"""Fenced Task032 interruption controls; seeded expiry is technical test evidence."""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_pedagogy_producer as f


class PedagogyRecoveryTests(unittest.TestCase):
    setUp = f.DurableTests.setUp
    tearDown = f.DurableTests.tearDown
    complete = f.DurableTests.complete

    def crash(self, phase, steps=7):
        class Crash(BaseException):
            pass

        def fault(current):
            if current == phase:
                raise Crash()

        for _ in range(steps - 1):
            self.port.work_once(self.p, self.run)
        with self.assertRaises(Crash):
            self.port.work_once(self.p, self.run, fault=fault)

    def expire_test_lease(self):
        # Seeded expiry exercises the existing fence; no timing/sleep assertion.
        with self.port.native(self.p, self.run, "read") as native:
            with native.leases.db:
                native.leases.db.execute(
                    "UPDATE director_leases SET expires_at=0 WHERE state='ACTIVE'")

    def repair(self):
        self.expire_test_lease()
        self.port.recover(self.p, self.run)
        result = self.complete()
        self.assertTrue(result["slice_complete"])
        self.assertEqual(result["stages"]["PEDAGOGY"], "SUCCEEDED")
        return result

    def test_candidate_publication_interruption(self):
        self.crash("after_PEDAGOGY_pedagogy.plan.candidates_cas")
        self.repair()

    def test_artifact_cas_publication_interruption(self):
        self.crash("after_PEDAGOGY_pedagogy.plan_cas")
        self.repair()

    def test_terminal_before_queue_ack(self):
        self.crash("after_PEDAGOGY_terminal")
        with self.port.native(self.p, self.run, "read") as native:
            before = native.persistence.load_run_state(self.run)["stages"]["PEDAGOGY"]["attempts"][-1]
            output = before["output_artifact_refs"]
            self.assertEqual(before["state"], "SUCCEEDED")
            self.assertEqual(native.queue.get(native.task_id(self.run, "PEDAGOGY", before["attempt"])).state,
                             "DELIVERED")
        self.repair()
        with self.port.native(self.p, self.run, "read") as native:
            after = native.persistence.load_run_state(self.run)["stages"]["PEDAGOGY"]["attempts"][-1]
            self.assertEqual(after["output_artifact_refs"], output)
            self.assertEqual(after["attempt"], before["attempt"])
            self.assertEqual(native.queue.get(native.task_id(self.run, "PEDAGOGY", after["attempt"])).state,
                             "ACKED")

    def test_success_before_downstream_admission_boundary(self):
        self.crash("before_next_admission")
        result = self.complete()
        self.assertTrue(result["slice_complete"])
        self.assertTrue(all(state == "NOT_RUN" for state in result["downstream"].values()))

    def test_reasoning_success_before_pedagogy_admission(self):
        self.crash("before_next_admission", steps=6)
        result = self.complete()
        self.assertEqual(result["stages"]["PEDAGOGY"], "SUCCEEDED")

    def test_active_lease_cannot_be_recovered(self):
        self.crash("after_PEDAGOGY_pedagogy.plan_cas")
        with self.assertRaises(Exception):
            self.port.recover(self.p, self.run)

    def test_stale_pedagogy_writer_rejected(self):
        with self.port.native(self.p, self.run, "read") as native:
            native.active_lease = native.leases.acquire("expired-pedagogy", "intent", native.owner,
                                                        now=0, ttl_seconds=1)
            with self.assertRaises(Exception):
                native.put(self.run, "PEDAGOGY", "pedagogy.plan", {})

    def test_competing_live_worker_fails_closed(self):
        for _ in range(6):
            self.port.work_once(self.p, self.run)
        with self.port.native(self.p, self.run, "read") as native:
            config = native.configuration(self.run, self.p.tenant)
            task_id = native.task_id(self.run, "PEDAGOGY", 1)
            native.leases.acquire(task_id, config["fingerprint"], "competing-live-owner", ttl_seconds=120)
        with self.assertRaises(Exception):
            self.port.work_once(self.p, self.run)
        with self.port.native(self.p, self.run, "read") as native:
            self.assertNotEqual(native.queue.get(task_id).state, "ACKED")
            attempt = native.persistence.load_run_state(self.run)["stages"]["PEDAGOGY"]["attempts"][-1]
            self.assertNotEqual(attempt["state"], "SUCCEEDED")

    def test_interrupted_attempt_and_evidence_retained(self):
        self.crash("after_PEDAGOGY_pedagogy.plan_cas")
        self.repair()
        with self.port.native(self.p, self.run, "read") as native:
            rows = native.persistence.load_run_state(self.run)["stages"]["PEDAGOGY"]["attempts"]
            self.assertEqual([row["state"] for row in rows], ["FAILED", "SUCCEEDED"])
            self.assertTrue(rows[0]["evidence_refs"])
            self.assertEqual(native.queue.get(native.task_id(self.run, "PEDAGOGY", rows[0]["attempt"])).state,
                             "DEAD_LETTER")

    def test_terminal_tamper_prevents_ack(self):
        self.crash("after_PEDAGOGY_terminal")
        with self.port.native(self.p, self.run, "read") as native:
            attempt = native.persistence.load_run_state(self.run)["stages"]["PEDAGOGY"]["attempts"][-1]
            record = native.record(self.run, attempt["output_artifact_refs"][0])
            native.cas._path(record.blob_digest).write_bytes(b"tampered-test-payload")
        self.expire_test_lease()
        with self.assertRaises(Exception):
            self.port.recover(self.p, self.run)
        with self.port.native(self.p, self.run, "read") as native:
            self.assertEqual(native.queue.get(native.task_id(self.run, "PEDAGOGY", 1)).state, "DELIVERED")

    def test_semantic_forgery_prevents_recovery_ack(self):
        self.crash("after_PEDAGOGY_terminal")
        with self.port.native(self.p, self.run, "read") as native:
            attempt = native.persistence.load_run_state(self.run)["stages"]["PEDAGOGY"]["attempts"][-1]
            old = attempt["output_artifact_refs"][0]
            record = native.record(self.run, old)
            forged = native.read(self.run, old)
            forged["metadata"]["instructional"]["product_accepted"] = True
            replacement = native.put(self.run, "PEDAGOGY", "pedagogy.plan", forged,
                                     record.parent_artifact_ids)
            with native.persistence._conn() as db:
                db.execute("UPDATE attempts SET output_refs_json=? WHERE stage_id='PEDAGOGY' AND attempt=1",
                           (json.dumps([replacement]),))
        self.expire_test_lease()
        with self.assertRaises(Exception):
            self.port.recover(self.p, self.run)
        with self.port.native(self.p, self.run, "read") as native:
            self.assertEqual(native.queue.get(native.task_id(self.run, "PEDAGOGY", 1)).state, "DELIVERED")

    def test_completed_identity_recovery(self):
        expected = self.complete()
        self.assertEqual(self.port.recover(self.p, self.run), expected)
        with self.port.native(self.p, self.run, "read") as native:
            native.director_inputs(self.run, self.p.tenant)
            attempts = native.persistence.load_run_state(self.run)["stages"]["PEDAGOGY"]["attempts"]
            self.assertEqual(len(attempts), 1)

    def test_dependency_scope_drift_rejected(self):
        with self.port.native(self.p, self.run, "read") as native:
            with native.persistence._conn() as db:
                db.execute("UPDATE stages SET required_predecessors_json='[]' WHERE stage_id='PEDAGOGY'")
            with self.assertRaisesRegex(Exception, "producer_profile_scope_mismatch"):
                native.work_once(self.run, self.p.tenant)


if __name__ == "__main__":
    unittest.main()
