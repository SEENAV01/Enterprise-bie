from __future__ import annotations

from unittest.mock import patch

import apps.api.job_service as native_jobs
from bie.app_product.contracts import ControlConflict
from .support import AppProductCase


class RetryControlTests(AppProductCase):
    def transient_failure(self):
        job_id = self.create(key="transient-key").job_id
        with patch.object(native_jobs, "inspect_real_pdf_toc", side_effect=RuntimeError("transient")):
            self.assertEqual(self.service.run_once().outcome, "FAILED")
        return job_id

    def test_retry_requires_failure(self):
        job_id = self.create().job_id
        with self.assertRaises(ControlConflict):
            self.service.retry(job_id)

    def test_failed_dead_letter_can_be_requeued(self):
        job_id = self.transient_failure()
        receipt = self.service.retry(job_id, "operator_retry_after_transient")
        self.assertEqual(receipt.queue_state, "READY")
        self.assertEqual(receipt.state, "RETRY_QUEUED")

    def test_retry_executes_real_worker_again(self):
        job_id = self.transient_failure()
        self.service.retry(job_id)
        self.assertEqual(self.service.run_once().outcome, "ACKED")
        self.assertEqual(self.service.status(job_id).status, "SUCCEEDED")

    def test_retry_event_is_persisted(self):
        job_id = self.transient_failure()
        self.service.retry(job_id, "retry_reason")
        events = self.service.timeline(job_id).control_events
        self.assertEqual(events[-1]["action"], "RETRY")
        self.assertEqual(events[-1]["reason"], "retry_reason")

    def test_duplicate_retry_before_worker_is_rejected(self):
        job_id = self.transient_failure()
        self.service.retry(job_id)
        with self.assertRaises(ControlConflict):
            self.service.retry(job_id)

    def test_cancelled_run_cannot_retry(self):
        job_id = self.create(key="cancel-before-run").job_id
        self.service.cancel(job_id)
        with self.assertRaises(ControlConflict):
            self.service.retry(job_id)

    def test_retry_survives_restart_before_execution(self):
        job_id = self.transient_failure()
        self.service.retry(job_id)
        self.service.close()
        from bie.app_product.service import OperatorService
        self.service = OperatorService(self.root)
        self.assertEqual(self.service.native.queue.get("inspect-" + job_id[4:]).state, "READY")
        self.assertEqual(self.service.run_once().outcome, "ACKED")


if __name__ == "__main__":
    import unittest
    unittest.main()
