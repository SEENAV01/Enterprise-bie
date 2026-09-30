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

    def test_failed_run_retry_creates_new_canonical_child(self):
        parent = self.transient_failure()
        receipt = self.service.retry(parent, "operator_retry_after_transient")
        self.assertEqual(receipt.queue_state, "READY")
        self.assertEqual(receipt.state, "RETRY_QUEUED")
        self.assertIsNotNone(receipt.related_job_id)
        self.assertNotEqual(parent, receipt.related_job_id)
        self.assertEqual(self.service.native.queue.get("inspect-" + parent[4:]).state, "DEAD_LETTER")

    def test_retry_executes_real_worker_on_child(self):
        parent = self.transient_failure()
        receipt = self.service.retry(parent)
        child = receipt.related_job_id
        self.assertEqual(self.service.run_once().outcome, "ACKED")
        self.assertEqual(self.service.status(child).status, "SUCCEEDED")
        self.assertEqual(self.service.status(parent).status, "FAILED")

    def test_retry_preserves_parent_failure_evidence(self):
        parent = self.transient_failure()
        before = self.service.failure(parent).to_safe_dict()
        receipt = self.service.retry(parent)
        self.service.run_once()
        self.assertEqual(self.service.failure(parent).to_safe_dict(), before)
        self.assertEqual(self.service.status(receipt.related_job_id).status, "SUCCEEDED")

    def test_retry_event_is_persisted_with_child_link(self):
        parent = self.transient_failure()
        receipt = self.service.retry(parent, "retry_reason")
        events = self.service.timeline(parent).control_events
        self.assertEqual(events[-1]["action"], "RETRY")
        self.assertEqual(events[-1]["reason"], "retry_reason")
        self.assertEqual(events[-1]["related_job_id"], receipt.related_job_id)

    def test_retry_lineage_is_durable(self):
        parent = self.transient_failure()
        receipt = self.service.retry(parent)
        links = self.service.operator.retries(parent)
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]["child_job_id"], receipt.related_job_id)

    def test_duplicate_retry_while_child_ready_is_rejected(self):
        parent = self.transient_failure()
        self.service.retry(parent)
        with self.assertRaises(ControlConflict):
            self.service.retry(parent)

    def test_cancelled_run_cannot_retry(self):
        job_id = self.create(key="cancel-before-run").job_id
        self.service.cancel(job_id)
        with self.assertRaises(ControlConflict):
            self.service.retry(job_id)

    def test_retry_survives_restart_before_execution(self):
        parent = self.transient_failure()
        receipt = self.service.retry(parent)
        child = receipt.related_job_id
        self.service.close()
        from bie.app_product.service import OperatorService
        self.service = OperatorService(self.root)
        self.assertEqual(self.service.native.queue.get("inspect-" + child[4:]).state, "READY")
        self.assertEqual(self.service.operator.retries(parent)[0]["child_job_id"], child)
        self.assertEqual(self.service.run_once().outcome, "ACKED")
        self.assertEqual(self.service.status(child).status, "SUCCEEDED")

    def test_retry_source_hash_matches_parent(self):
        parent = self.transient_failure()
        receipt = self.service.retry(parent)
        self.assertEqual(
            self.service.status(parent).source_hash,
            self.service.status(receipt.related_job_id).source_hash,
        )


if __name__ == "__main__":
    import unittest
    unittest.main()
