"""Fenced interrupted publication controls using canonical stores, no mocks."""
import unittest
import secrets
import sys
import time
from pathlib import Path
from .test_scene_ir_producer import PreparedSceneFixture
from .recovery_observations import record_observation


class WorkerInterrupted(BaseException):
    """Unit-level process-loss stand-in; actual process proof is separate."""


class SceneRecoveryControls(PreparedSceneFixture):
    def crash(self, phase):
        def fault(name):
            if name == phase:
                raise WorkerInterrupted()
        with self.assertRaises(WorkerInterrupted):
            self.port.work_once(self.p, self.run, director_stack=self.stack, fault=fault)

    def expire_test_lease(self):
        # Test-owned stores only. Production recovery must wait for real expiry;
        # no force-lease operation or new native recovery contract is introduced.
        with self.port.native(self.p, self.run, "read") as service:
            with service.leases.db:
                service.leases.db.execute("UPDATE director_leases SET expires_at=0 WHERE state='ACTIVE'")

    def recover(self):
        self.expire_test_lease()
        self.port.recover(self.p, self.run)
        result = self.step()
        self.assertEqual(result["stages"]["SCENE_IR"], "SUCCEEDED", result.get("safe_diagnostics"))
        self.assertEqual(self.stack.calls, dict(generator=0, critic=0, annotator=0, reviewer=0))
        with self.port.native(self.p, self.run, "read") as service:
            _, receipt = service.verified_scene_ir(self.run, self.p.tenant)
            history = service.persistence.load_run_state(self.run)["stages"]["SCENE_IR"]["attempts"]
            self.assertEqual(history[-1]["state"], "SUCCEEDED")
            self.assertEqual(service.queue.get(service.task_id(self.run, "SCENE_IR", history[-1]["attempt"])).state, "ACKED")
            return receipt

    def phase(self, name):
        self.crash(name)
        self.recover()
        with self.port.native(self.p, self.run, "read") as service:
            history = service.persistence.load_run_state(self.run)["stages"]["SCENE_IR"]["attempts"]
            self.assertEqual([a["state"] for a in history], ["FAILED", "SUCCEEDED"])
            self.assertEqual(service.queue.get(service.task_id(self.run, "SCENE_IR", 1)).state, "DEAD_LETTER")

    def test_after_inputs_verified(self):
        self.phase("after_SCENE_IR_inputs_verified")

    def test_after_catalog(self):
        self.phase("after_SCENE_IR_catalog")

    def test_after_adoption(self):
        self.phase("after_SCENE_IR_adoption")

    def test_after_codec_and_native_validation(self):
        self.phase("after_SCENE_IR_validation")

    def test_after_private_publication(self):
        self.phase("after_SCENE_IR_private_publication")

    def test_after_document_cas(self):
        self.phase("after_SCENE_IR_scene.ir_cas")

    def test_after_private_validation_cas(self):
        self.phase("after_SCENE_IR_scene_ir.validation_cas")

    def test_before_terminal(self):
        self.phase("before_SCENE_IR_terminal")

    def test_after_terminal_before_ack_exact_identity(self):
        self.crash("after_SCENE_IR_terminal")
        with self.port.native(self.p, self.run, "read") as service:
            before = service.verified_scene_ir(self.run, self.p.tenant)
            self.assertEqual(service.queue.get(service.task_id(self.run, "SCENE_IR", 1)).state, "DELIVERED")
        self.recover()
        with self.port.native(self.p, self.run, "read") as service:
            self.assertEqual(service.verified_scene_ir(self.run, self.p.tenant), before)
            self.assertEqual(len(service.persistence.load_run_state(self.run)["stages"]["SCENE_IR"]["attempts"]), 1)

    def test_ack_before_next_admission_never_runs_video(self):
        self.crash("before_next_admission")
        result = self.recover()
        self.assertTrue(result["requires_review"])
        self.assertFalse(result["video_code_executed"])

    def test_live_lease_not_overridden(self):
        self.crash("after_SCENE_IR_catalog")
        with self.assertRaises(Exception):
            self.port.recover(self.p, self.run)

    def actual_process_loss(self, phase):
        from apps.operator.process_supervision import supervise, child_environment
        from apps.operator.process_limits import PdfProcessBudget
        token = secrets.token_urlsafe(40)
        env = child_environment(); env['BIE_OPERATOR_TOKEN'] = token
        worker = Path(__file__).with_name('recovery_worker.py')
        command = [sys.executable, '-I', '-B', str(worker), '--root', str(self.root), '--run', self.run]
        started = time.monotonic()
        first = supervise(command + ['--phase', phase], env, PdfProcessBudget())
        record_observation(first, self.root, phase, 'CRASH', time.monotonic() - started)
        # Preserve every original assertion; the closed observation only makes
        # a rejection diagnosable. It is never a successful crash witness.
        self.assertTrue(first.completed)
        self.assertEqual(first.exit_code, 73)
        before = None
        if phase == 'after_SCENE_IR_terminal':
            with self.port.native(self.p, self.run, 'read') as service:
                before = service.verified_scene_ir(self.run, self.p.tenant)
        self.expire_test_lease()
        started = time.monotonic()
        second = supervise(command + ['--recover'], env, PdfProcessBudget())
        record_observation(second, self.root, phase, 'RECOVER', time.monotonic() - started)
        self.assertTrue(second.completed)
        self.assertEqual(second.exit_code, 0)
        with self.port.native(self.p, self.run, 'read') as service:
            final = service.verified_scene_ir(self.run, self.p.tenant)
            history = service.persistence.load_run_state(self.run)['stages']['SCENE_IR']['attempts']
            if before is not None:
                self.assertEqual(final, before)
                self.assertEqual(len(history), 1)
            else:
                self.assertEqual([a['state'] for a in history], ['FAILED', 'SUCCEEDED'])
            task = service.queue.get(service.task_id(self.run, 'SCENE_IR', history[-1]['attempt']))
            self.assertEqual(task.state, 'ACKED')

    def test_actual_process_loss_after_private_publication(self):
        self.actual_process_loss('after_SCENE_IR_private_publication')

    def test_actual_process_loss_after_terminal_before_ack(self):
        self.actual_process_loss('after_SCENE_IR_terminal')


if __name__ == "__main__":
    unittest.main()
