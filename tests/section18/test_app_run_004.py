from __future__ import annotations

from batch001_support import OperatorCase

from bie.product_app_v1.run_status import RunStatusService


class AppRun004Tests(OperatorCase):
    def test_draft_status_is_operator_owned(self):
        run = self.create("draft-status")
        status = RunStatusService(self.context).status(run["run_id"])
        self.assertEqual(status["state"], "DRAFT")
        self.assertEqual(status["status_source"], "operator_store")

    def test_ready_status_reads_canonical_job(self):
        result = self.imported("ready-status")
        status = self.observe(result["run"]["run_id"])
        self.assertEqual(status["canonical_status"], "READY")
        self.assertEqual(status["queue_state"], "READY")
        self.assertEqual(status["status_source"], "canonical_job_service")

    def test_success_is_reconciled_from_canonical_job(self):
        result = self.imported("success-status")
        run_id = result["run"]["run_id"]
        self.run_native_once()
        status = self.observe(run_id)
        self.assertEqual(status["state"], "SUCCEEDED")
        self.assertTrue(status["result_available"])

    def test_failure_is_reconciled_from_canonical_job(self):
        run_id = self.fail_run("failed-status")
        status = self.observe(run_id)
        self.assertEqual(status["state"], "FAILED")
        self.assertEqual(status["canonical_status"], "FAILED")

    def test_status_reconciliation_is_persisted(self):
        result = self.imported("persist-status")
        run_id = result["run"]["run_id"]
        self.run_native_once()
        self.observe(run_id)
        self.assertEqual(self.context.operator.get_run(run_id).state, "SUCCEEDED")

    def test_no_fabricated_percentage(self):
        result = self.imported("percent-status")
        status = self.observe(result["run"]["run_id"])
        self.assertIsNone(status["progress_percent"])

    def test_result_not_claimed_before_success(self):
        result = self.imported("notready-status")
        status = self.observe(result["run"]["run_id"])
        self.assertFalse(status["result_available"])

    def test_restart_reads_same_canonical_status(self):
        result = self.imported("restart-status")
        run_id = result["run"]["run_id"]
        from bie.product_app_v1.context import OperatorContext
        reopened = OperatorContext(self.root)
        status = RunStatusService(reopened).status(run_id)
        self.assertEqual(status["state"], "READY")


if __name__ == "__main__":
    import unittest
    unittest.main()
