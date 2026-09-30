from __future__ import annotations

from unittest.mock import patch

from apps.api import job_service as jobs_module

from tests.section18.support import Section18Case


class StatusTimelineFailureTests(Section18Case):
    def test_001_ready_status_is_backend_derived(self):
        run = self.create()
        value = self.client.get("/v1/app/runs/" + run["job_id"]).json()
        self.assertEqual(value["status"], "READY")
        self.assertEqual(value["canonical_status"], "READY")
        self.assertFalse(value["result_available"])

    def test_002_timeline_contains_persisted_source_transition(self):
        run = self.create()
        timeline = self.client.get("/v1/app/runs/" + run["job_id"] + "/timeline").json()
        self.assertGreaterEqual(timeline["event_count"], 1)
        self.assertTrue(any(row["to_state"] == "READY" for row in timeline["events"]))

    def test_003_success_timeline_records_running_and_succeeded(self):
        run = self.create()
        service = self.service()
        try:
            self.assertEqual(service.run_once().outcome, "ACKED")
        finally:
            service.close()
        timeline = self.client.get("/v1/app/runs/" + run["job_id"] + "/timeline").json()
        states = [row["to_state"] for row in timeline["events"] if row["event_kind"] == "stage"]
        self.assertIn("RUNNING", states)
        self.assertIn("SUCCEEDED", states)

    def test_004_success_status_reports_result_only_after_worker(self):
        run = self.create()
        service = self.service()
        try:
            service.run_once()
        finally:
            service.close()
        value = self.client.get("/v1/app/runs/" + run["job_id"]).json()
        self.assertEqual(value["status"], "SUCCEEDED")
        self.assertTrue(value["result_available"])
        self.assertEqual(value["run_state"], "EXECUTION_COMPLETE")

    def test_005_failure_view_is_empty_before_failure(self):
        run = self.create()
        value = self.client.get("/v1/app/runs/" + run["job_id"] + "/failure").json()
        self.assertFalse(value["failure_available"])
        self.assertEqual(value["diagnostic_codes"], [])
        self.assertEqual(value["evidence_refs"], [])

    def test_006_controlled_worker_failure_is_persisted(self):
        run = self.create()
        service = self.service()
        try:
            with patch.object(jobs_module, "inspect_real_pdf_toc", side_effect=RuntimeError("secret detail")):
                self.assertEqual(service.run_once().outcome, "FAILED")
        finally:
            service.close()
        value = self.client.get("/v1/app/runs/" + run["job_id"] + "/failure").json()
        self.assertTrue(value["failure_available"])
        self.assertEqual(value["diagnostic_codes"], ["internal_worker_error"])
        self.assertTrue(value["retryable"])

    def test_007_failure_view_does_not_expose_exception_text(self):
        run = self.create()
        service = self.service()
        try:
            with patch.object(jobs_module, "inspect_real_pdf_toc", side_effect=RuntimeError("TOP SECRET")):
                service.run_once()
        finally:
            service.close()
        response = self.client.get("/v1/app/runs/" + run["job_id"] + "/failure")
        self.assertNotIn("TOP SECRET", response.text)
        self.assertNotIn("RuntimeError", response.text)
        self.assertFalse(response.json()["raw_exception_exposed"])

    def test_008_unknown_run_returns_safe_404(self):
        response = self.client.get("/v1/app/runs/job-missing")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "job_not_found")

    def test_009_timeline_survives_restart(self):
        run = self.create()
        first = self.client.get("/v1/app/runs/" + run["job_id"] + "/timeline").json()
        second = self.client.get("/v1/app/runs/" + run["job_id"] + "/timeline").json()
        self.assertEqual(first, second)

    def test_010_status_never_claims_product_acceptance(self):
        run = self.create()
        self.assertFalse(self.client.get("/v1/app/runs/" + run["job_id"]).json()["product_accepted"])


if __name__ == "__main__":
    import unittest
    unittest.main()
