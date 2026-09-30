from __future__ import annotations

from apps.api.job_service import JobNotFound
from .support import AppProductCase


class RunStatusTests(AppProductCase):
    def test_ready_status_matches_canonical_state(self):
        view = self.create()
        self.assertEqual((view.status, view.canonical_status, view.queue_state), ("READY", "READY", "READY"))

    def test_success_status_after_actual_worker(self):
        job_id = self.create().job_id
        self.assertEqual(self.service.run_once().outcome, "ACKED")
        view = self.service.status(job_id)
        self.assertEqual(view.status, "SUCCEEDED")
        self.assertEqual(view.queue_state, "ACKED")
        self.assertTrue(view.result_available)

    def test_status_source_hash_stays_bound(self):
        initial = self.create()
        self.service.run_once()
        final = self.service.status(initial.job_id)
        self.assertEqual(initial.source_hash, final.source_hash)

    def test_unknown_run_is_not_fabricated(self):
        with self.assertRaises(JobNotFound):
            self.service.status("job-" + "a" * 64)

    def test_ready_never_claims_result_available(self):
        self.assertFalse(self.create().result_available)

    def test_status_survives_service_restart(self):
        job_id = self.create().job_id
        self.service.close()
        from bie.app_product.service import OperatorService
        self.service = OperatorService(self.root)
        self.assertEqual(self.service.status(job_id).status, "READY")

    def test_status_after_completed_restart(self):
        job_id = self.create().job_id
        self.service.run_once()
        self.service.close()
        from bie.app_product.service import OperatorService
        self.service = OperatorService(self.root)
        self.assertEqual(self.service.status(job_id).status, "SUCCEEDED")

    def test_status_is_safe_dict(self):
        view = self.create()
        self.assertEqual(set(view.to_safe_dict()), {
            "job_id", "status", "canonical_status", "queue_state",
            "source_hash", "result_available", "control_state",
        })


if __name__ == "__main__":
    import unittest
    unittest.main()
