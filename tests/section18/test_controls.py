from __future__ import annotations

from unittest.mock import patch

from apps.api import job_service as jobs_module

from tests.section18.support import Section18Case


class ControlTests(Section18Case):
    def test_001_pause_changes_effective_state_not_canonical_stage(self):
        run = self.create()
        response = self.client.post("/v1/app/runs/" + run["job_id"] + "/pause")
        self.assertEqual(response.status_code, 200)
        value = response.json()
        self.assertEqual(value["status"], "PAUSED")
        self.assertEqual(value["canonical_status"], "READY")
        self.assertEqual(value["control_state"], "PAUSED")

    def test_002_paused_worker_does_not_execute_source(self):
        run = self.create()
        self.client.post("/v1/app/runs/" + run["job_id"] + "/pause")
        service = self.service()
        try:
            with patch.object(jobs_module, "inspect_real_pdf_toc", wraps=jobs_module.inspect_real_pdf_toc) as inspect:
                outcome = service.run_once()
            self.assertEqual(outcome.outcome, "PAUSED")
            inspect.assert_not_called()
            self.assertEqual(service.status(run["job_id"])["canonical_status"], "READY")
        finally:
            service.close()

    def test_003_resume_returns_run_to_active_control(self):
        run = self.create()
        self.client.post("/v1/app/runs/" + run["job_id"] + "/pause")
        response = self.client.post("/v1/app/runs/" + run["job_id"] + "/resume")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["control_state"], "ACTIVE")
        self.assertEqual(response.json()["status"], "READY")

    def test_004_resume_then_worker_can_complete(self):
        run = self.create()
        self.client.post("/v1/app/runs/" + run["job_id"] + "/pause")
        service = self.service()
        try:
            self.assertEqual(service.run_once().outcome, "PAUSED")
        finally:
            service.close()
        self.client.post("/v1/app/runs/" + run["job_id"] + "/resume")
        service = self.service()
        try:
            self.assertEqual(service.run_once().outcome, "ACKED")
        finally:
            service.close()
        self.assertEqual(self.client.get("/v1/app/runs/" + run["job_id"]).json()["status"], "SUCCEEDED")

    def test_005_cancel_ready_run_is_terminal_and_dead_lettered(self):
        run = self.create()
        response = self.client.post("/v1/app/runs/" + run["job_id"] + "/cancel")
        self.assertEqual(response.status_code, 200)
        value = response.json()
        self.assertEqual(value["status"], "CANCELLED")
        self.assertEqual(value["canonical_status"], "BLOCKED")
        self.assertEqual(value["queue_state"], "DEAD_LETTER")

    def test_006_cancel_records_safe_evidence(self):
        run = self.create()
        self.client.post("/v1/app/runs/" + run["job_id"] + "/cancel")
        failure = self.client.get("/v1/app/runs/" + run["job_id"] + "/failure").json()
        self.assertTrue(failure["failure_available"])
        self.assertEqual(failure["diagnostic_codes"], ["cancelled_by_operator"])
        self.assertFalse(failure["retryable"])
        self.assertEqual(len(failure["evidence_refs"]), 1)

    def test_007_cancel_during_runtime_discards_result(self):
        run = self.create()
        service = self.service()
        real = jobs_module.inspect_real_pdf_toc
        def inspection(data):
            service.cancel(run["job_id"])
            return real(data)
        try:
            with patch.object(jobs_module, "inspect_real_pdf_toc", side_effect=inspection):
                outcome = service.run_once()
            self.assertEqual(outcome.outcome, "CANCELLED")
            status = service.status(run["job_id"])
            self.assertEqual(status["canonical_status"], "BLOCKED")
            self.assertFalse(status["result_available"])
            self.assertNotIn("result-" + run["job_id"][4:], service.persistence.artifacts_for_run(run["job_id"]))
        finally:
            service.close()

    def test_008_retry_creates_new_attempt_and_new_queue_identity(self):
        run = self.create()
        service = self.service()
        try:
            with patch.object(jobs_module, "inspect_real_pdf_toc", side_effect=RuntimeError("seeded")):
                self.assertEqual(service.run_once().outcome, "FAILED")
        finally:
            service.close()
        response = self.client.post("/v1/app/runs/" + run["job_id"] + "/retry")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["attempt"], 2)
        self.assertEqual(response.json()["canonical_status"], "READY")
        self.assertEqual(response.json()["queue_state"], "READY")

    def test_009_retry_after_transient_failure_can_succeed(self):
        run = self.create()
        service = self.service()
        try:
            with patch.object(jobs_module, "inspect_real_pdf_toc", side_effect=RuntimeError("transient")):
                service.run_once()
        finally:
            service.close()
        self.client.post("/v1/app/runs/" + run["job_id"] + "/retry")
        service = self.service()
        try:
            self.assertEqual(service.run_once().outcome, "ACKED")
            self.assertEqual(service.status(run["job_id"])["attempt"], 2)
            self.assertEqual(service.status(run["job_id"])["status"], "SUCCEEDED")
        finally:
            service.close()

    def test_010_retry_preserves_first_failure_evidence(self):
        run = self.create()
        service = self.service()
        try:
            with patch.object(jobs_module, "inspect_real_pdf_toc", side_effect=RuntimeError("transient")):
                service.run_once()
            first = service.failure_view(run["job_id"])["evidence_refs"][0]
        finally:
            service.close()
        self.client.post("/v1/app/runs/" + run["job_id"] + "/retry")
        service = self.service()
        try:
            service.run_once()
            self.assertIn(first, service.persistence.evidence_for_run(run["job_id"]))
            self.assertGreaterEqual(len(service.persistence.evidence_for_run(run["job_id"])), 2)
        finally:
            service.close()

    def test_011_retry_is_rejected_for_ready_run(self):
        run = self.create()
        response = self.client.post("/v1/app/runs/" + run["job_id"] + "/retry")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "retry_requires_failed_job")

    def test_012_pause_is_rejected_after_success(self):
        run = self.create()
        service = self.service()
        try:
            service.run_once()
        finally:
            service.close()
        self.assertEqual(self.client.post("/v1/app/runs/" + run["job_id"] + "/pause").status_code, 409)

    def test_013_control_events_are_present_in_timeline(self):
        run = self.create()
        self.client.post("/v1/app/runs/" + run["job_id"] + "/pause")
        self.client.post("/v1/app/runs/" + run["job_id"] + "/resume")
        timeline = self.client.get("/v1/app/runs/" + run["job_id"] + "/timeline").json()
        controls = [row for row in timeline["events"] if row["event_kind"] == "control"]
        self.assertEqual([row["to_state"] for row in controls], ["PAUSED", "ACTIVE"])


if __name__ == "__main__":
    import unittest
    unittest.main()
