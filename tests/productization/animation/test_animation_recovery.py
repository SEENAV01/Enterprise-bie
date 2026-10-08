"""Retained Animation attempts, real durable CAS, fencing and restart controls."""
from contextlib import closing
import sqlite3
import unittest

from test_animation_producer import PreparedAnimationFixture
from bie.productization.director_storage import native_runtime


class WorkerInterrupted(BaseException):
    """Bounded process-loss stand-in outside ordinary stage failure handling."""


class AnimationRecoveryTests(PreparedAnimationFixture):
    def crash(self, phase):
        self.until_animation()
        def fault(current):
            if current == phase:
                raise WorkerInterrupted()
        with self.assertRaises(WorkerInterrupted):
            self.step(fault=fault)

    def expire_test_lease(self):
        with self.port.native(self.p, self.run, "read") as service:
            with service.leases.db:
                service.leases.db.execute("UPDATE director_leases SET expires_at=0 WHERE state='ACTIVE'")

    def recover_and_finish(self):
        self.expire_test_lease()
        self.port.recover(self.p, self.run)
        result = self.step()
        self.assertTrue(result["slice_complete"], result.get("safe_diagnostics"))
        self.assertEqual(result["stages"]["ANIMATION"], "SUCCEEDED")
        self.assertTrue(all(v == "NOT_RUN" for v in result["downstream"].values()))
        self.assertEqual(self.stack.calls, dict(generator=0, critic=0, annotator=0, reviewer=0))
        return result

    def assert_retained_interruption(self):
        with self.port.native(self.p, self.run, "read") as service:
            history = service.persistence.load_run_state(self.run)["stages"]["ANIMATION"]["attempts"]
            self.assertEqual([row["state"] for row in history], ["FAILED", "SUCCEEDED"])
            self.assertTrue(history[0]["evidence_refs"])
            recovery = service.read(self.run, history[0]["evidence_refs"][-1])
            self.assertEqual(recovery["code"], "interrupted_attempt")
            self.assertEqual(service.queue.get(service.task_id(self.run, "ANIMATION", 1)).state, "DEAD_LETTER")
            self.assertEqual(service.queue.get(service.task_id(self.run, "ANIMATION", 2)).state, "ACKED")

    def candidate_identity(self):
        with self.port.native(self.p, self.run, "read") as service:
            with native_runtime(service, self.run, None) as runtime:
                rows = [row for row in runtime.io.catalog.records.values()
                        if row.artifact_type == "director.animation_sync_candidate"]
                self.assertEqual(len(rows), 1)
                return runtime.io.load(rows[0].artifact_id).to_ref()

    def interrupted_phase(self, phase):
        self.crash(phase)
        self.recover_and_finish()
        self.assert_retained_interruption()

    def test_current_visual_verification_interrupt_recovers(self):
        self.interrupted_phase("after_ANIMATION_visual_verified")

    def test_intent_derivation_interrupt_recovers(self):
        self.interrupted_phase("after_ANIMATION_intent_derivation")

    def test_native_sync_interrupt_reuses_exact_candidate(self):
        self.crash("after_ANIMATION_sync_candidate")
        before = self.candidate_identity()
        self.recover_and_finish()
        self.assert_retained_interruption()
        self.assertEqual(self.candidate_identity(), before)

    def test_semantic_domain_interrupt_recovers(self):
        self.interrupted_phase("after_ANIMATION_semantic_domain")

    def test_timeline_interrupt_recovers(self):
        self.interrupted_phase("after_ANIMATION_timeline")

    def test_qa_interrupt_recovers(self):
        self.interrupted_phase("after_ANIMATION_qa")

    def test_plan_build_interrupt_recovers(self):
        self.interrupted_phase("after_ANIMATION_plan")

    def test_sceneir_handoff_interrupt_recovers(self):
        self.interrupted_phase("after_ANIMATION_handoff")

    def test_plan_cas_before_terminal_interrupt_recovers(self):
        self.interrupted_phase("after_ANIMATION_animation.plan_cas")

    def test_private_validation_cas_interrupt_recovers(self):
        self.interrupted_phase("after_ANIMATION_animation.validation_cas")

    def test_before_terminal_interrupt_recovers(self):
        self.interrupted_phase("before_ANIMATION_terminal")

    def test_terminal_before_ack_preserves_exact_plan_identity(self):
        self.crash("after_ANIMATION_terminal")
        before = self.animation()
        with self.port.native(self.p, self.run, "read") as service:
            self.assertEqual(service.queue.get(service.task_id(self.run, "ANIMATION", 1)).state, "DELIVERED")
        self.recover_and_finish()
        self.assertEqual(self.animation(), before)
        with self.port.native(self.p, self.run, "read") as service:
            self.assertEqual(service.queue.get(service.task_id(self.run, "ANIMATION", 1)).state, "ACKED")
            self.assertEqual(len(service.persistence.load_run_state(self.run)["stages"]["ANIMATION"]["attempts"]), 1)

    def test_ack_boundary_never_admits_global_scene_ir(self):
        self.crash("before_next_admission")
        before = self.animation()
        result = self.step()
        self.assertTrue(result["slice_complete"])
        self.assertEqual(self.animation(), before)
        self.assertEqual(result["downstream"]["SCENE_IR"], "NOT_RUN")

    def test_live_lease_cannot_be_recovered(self):
        self.crash("after_ANIMATION_intent_derivation")
        with self.assertRaises(Exception):
            self.port.recover(self.p, self.run)

    def test_stale_writer_cannot_publish_animation_artifact(self):
        with self.port.native(self.p, self.run, "worker") as service:
            service.active_lease = service.leases.acquire("stale-animation-control", "intent",
                service.owner, now=0, ttl_seconds=1)
            with self.assertRaises(Exception):
                service.put(self.run, "ANIMATION", "animation.test_stale", dict(technical=True))

    def test_competing_live_worker_cannot_complete_or_ack(self):
        with self.port.native(self.p, self.run, "read") as service:
            cfg = service.configuration(self.run, self.p.tenant)
            task = service.task_id(self.run, "ANIMATION", 1)
            service.leases.acquire(task, cfg["fingerprint"], "other-worker", ttl_seconds=120)
        with self.assertRaises(Exception):
            self.step()
        with self.port.native(self.p, self.run, "read") as service:
            self.assertNotEqual(service.queue.get(task).state, "ACKED")

    def test_committed_tamper_prevents_recovery_ack(self):
        self.crash("after_ANIMATION_terminal")
        self.tamper_stage("ANIMATION")
        self.expire_test_lease()
        with self.assertRaises(Exception):
            self.port.recover(self.p, self.run)
        with self.port.native(self.p, self.run, "read") as service:
            self.assertEqual(service.queue.get(service.task_id(self.run, "ANIMATION", 1)).state, "DELIVERED")

    def test_sync_catalog_tamper_blocks_restart(self):
        self.assertTrue(self.step()["slice_complete"])
        _, receipt = self.animation()
        with self.port.native(self.p, self.run, "read") as service:
            with closing(sqlite3.connect(service.root / "director-catalog.sqlite3")) as db:
                with db:
                    db.execute("UPDATE artifact_records SET record_json='{}' WHERE artifact_id=?",
                               (receipt["sync_ref"]["artifact_id"],))
        with self.assertRaises(Exception):
            self.port.status(self.p, self.run)

    def test_completed_recovery_replays_without_new_attempt(self):
        expected = self.step()
        before = self.animation()
        self.assertEqual(self.port.recover(self.p, self.run), expected)
        self.assertEqual(self.animation(), before)

    def test_previous_visual_worker_cannot_consume_animation_task(self):
        from bie.productization.visual_slice import VisualProducerService
        with self.port.native(self.p, self.run, "read") as service:
            self.assertIsNone(service.queue.poll("wrong-profile", capability_tags=[VisualProducerService.capability]))
            self.assertEqual(service.queue.get(service.task_id(self.run, "ANIMATION", 1)).state, "READY")


if __name__ == "__main__":
    unittest.main()
