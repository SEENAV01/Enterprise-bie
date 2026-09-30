from __future__ import annotations

import json

from batch001_support import OperatorCase

from bie.product_app_v1.failure_view import FailureViewService, render_failure_view
from bie.product_app_v1.models import OperatorConflict


class AppRun006Tests(OperatorCase):
    def test_failed_run_exposes_safe_evidence(self):
        run_id = self.fail_run("failure-view")
        view = FailureViewService(self.context).failure(run_id)
        self.assertEqual(view["failure"]["status"], "FAILED")
        self.assertEqual(view["failure"]["diagnostic_code"], "pdf_inspection_failed")
        self.assertFalse(view["raw_source_exposed"])
        self.assertFalse(view["traceback_exposed"])

    def test_failure_view_requires_failed_state(self):
        result = self.imported("failure-not-yet")
        with self.assertRaises(OperatorConflict):
            FailureViewService(self.context).failure(result["run"]["run_id"])

    def test_failure_view_points_to_real_evidence_artifact(self):
        run_id = self.fail_run("failure-evidence")
        view = FailureViewService(self.context).failure(run_id)
        service = self.context.job_service()
        try:
            record = service.persistence.load_artifact(view["evidence_id"])
        finally:
            service.close()
        self.assertTrue(record.evidence)
        self.assertEqual(record.artifact_type, "document.inspection.evidence")

    def test_failure_view_does_not_expose_source_text(self):
        run_id = self.fail_run("failure-no-source")
        serialized = json.dumps(FailureViewService(self.context).failure(run_id), sort_keys=True)
        self.assertNotIn("%PDF-1.7", serialized)
        self.assertNotIn("malformed", serialized)

    def test_failure_view_does_not_expose_exception_detail(self):
        result = self.imported("failure-unexpected")
        run_id = result["run"]["run_id"]
        import apps.api.job_service as jobs_module
        from unittest.mock import patch
        service = self.context.job_service()
        try:
            with patch.object(jobs_module, "inspect_real_pdf_toc", side_effect=RuntimeError("super-secret-stack")):
                self.assertEqual(service.run_once("failure-worker").outcome, "FAILED")
        finally:
            service.close()
        self.observe(run_id)
        serialized = json.dumps(FailureViewService(self.context).failure(run_id), sort_keys=True)
        self.assertNotIn("super-secret-stack", serialized)
        self.assertIn("internal_worker_error", serialized)

    def test_failure_survives_restart(self):
        run_id = self.fail_run("failure-restart")
        from bie.product_app_v1.context import OperatorContext
        reopened = OperatorContext(self.root)
        view = FailureViewService(reopened).failure(run_id)
        self.assertEqual(view["failure"]["status"], "FAILED")

    def test_failure_html_has_accessible_title_and_safe_message(self):
        run_id = self.fail_run("failure-html")
        html = render_failure_view(FailureViewService(self.context).failure(run_id))
        self.assertIn("aria-labelledby='failure-title'", html)
        self.assertIn("No source document text or traceback", html)

    def test_failure_view_marks_retry_allowed_without_executing_retry(self):
        run_id = self.fail_run("failure-retry")
        view = FailureViewService(self.context).failure(run_id)
        self.assertTrue(view["retry_allowed"])
        self.assertEqual(self.context.operator.get_run(run_id).attempt, 1)


if __name__ == "__main__":
    import unittest
    unittest.main()
