from __future__ import annotations

from bie.app_product.contracts import ControlConflict
from .support import AppProductCase


class PauseCancelResumeTests(AppProductCase):
    def test_pause_ready_run_is_actual_queue_block(self):
        job_id = self.create().job_id
        receipt = self.service.pause(job_id)
        self.assertEqual(receipt.state, "PAUSED")
        self.assertEqual(self.service.native.queue.get("inspect-" + job_id[4:]).state, "DEAD_LETTER")
        self.assertEqual(self.service.run_once().outcome, "IDLE")

    def test_pause_status_is_truthful_overlay(self):
        job_id = self.create().job_id
        self.service.pause(job_id)
        view = self.service.status(job_id)
        self.assertEqual(view.status, "PAUSED")
        self.assertEqual(view.canonical_status, "READY")
        self.assertEqual(view.control_state, "PAUSED")

    def test_resume_redrives_paused_queue(self):
        job_id = self.create().job_id
        self.service.pause(job_id)
        receipt = self.service.resume(job_id)
        self.assertEqual((receipt.state, receipt.queue_state), ("ACTIVE", "READY"))
        self.assertEqual(self.service.run_once().outcome, "ACKED")

    def test_resume_requires_pause(self):
        job_id = self.create().job_id
        with self.assertRaises(ControlConflict):
            self.service.resume(job_id)

    def test_cancel_ready_run_blocks_worker(self):
        job_id = self.create().job_id
        receipt = self.service.cancel(job_id)
        self.assertEqual(receipt.state, "CANCELLED")
        self.assertEqual(self.service.run_once().outcome, "IDLE")
        self.assertEqual(self.service.status(job_id).status, "CANCELLED")

    def test_cancelled_run_cannot_resume(self):
        job_id = self.create().job_id
        self.service.cancel(job_id)
        with self.assertRaises(ControlConflict):
            self.service.resume(job_id)

    def test_pause_then_cancel_is_terminal(self):
        job_id = self.create().job_id
        self.service.pause(job_id)
        self.service.cancel(job_id)
        self.assertEqual(self.service.status(job_id).control_state, "CANCELLED")
        with self.assertRaises(ControlConflict):
            self.service.pause(job_id)

    def test_control_events_survive_restart(self):
        job_id = self.create().job_id
        self.service.pause(job_id)
        self.service.resume(job_id)
        before = self.service.timeline(job_id).control_events
        self.service.close()
        from bie.app_product.service import OperatorService
        self.service = OperatorService(self.root)
        self.assertEqual(self.service.timeline(job_id).control_events, before)

    def test_pause_rejects_after_worker_claim(self):
        job_id = self.create().job_id
        delivery = self.service.native.queue.poll("claimed-worker", capability_tags=["pdf_inspection"])
        self.assertIsNotNone(delivery)
        with self.assertRaises(ControlConflict):
            self.service.pause(job_id)

    def test_cancel_rejects_after_worker_claim(self):
        job_id = self.create().job_id
        delivery = self.service.native.queue.poll("claimed-worker", capability_tags=["pdf_inspection"])
        self.assertIsNotNone(delivery)
        with self.assertRaises(ControlConflict):
            self.service.cancel(job_id)

    def test_completed_run_cannot_cancel(self):
        job_id = self.create().job_id
        self.service.run_once()
        with self.assertRaises(ControlConflict):
            self.service.cancel(job_id)

    def test_pause_is_idempotent_before_resume(self):
        job_id = self.create().job_id
        first = self.service.pause(job_id)
        second = self.service.pause(job_id)
        self.assertEqual(first.state, second.state)
        self.assertEqual(len(self.service.timeline(job_id).control_events), 1)


if __name__ == "__main__":
    import unittest
    unittest.main()
