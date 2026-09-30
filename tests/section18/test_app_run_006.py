from __future__ import annotations

import json
from unittest.mock import patch

import apps.api.job_service as native_jobs
from bie.app_product.contracts import ProjectionError
from .support import AppProductCase


class FailureViewTests(AppProductCase):
    def malformed(self):
        return self.service.create_run(
            b"%PDF-1.7\nmalformed",
            "malformed-key",
            "Broken.pdf",
        ).job_id

    def test_failure_view_requires_actual_failure(self):
        job_id = self.create().job_id
        with self.assertRaises(ProjectionError):
            self.service.failure(job_id)

    def test_malformed_source_failure_is_visible(self):
        job_id = self.malformed()
        self.assertEqual(self.service.run_once().outcome, "FAILED")
        view = self.service.failure(job_id)
        self.assertEqual(view.status, "FAILED")
        self.assertIn("pdf_inspection_failed", view.diagnostics)

    def test_failure_view_binds_evidence_reference(self):
        job_id = self.malformed()
        self.service.run_once()
        view = self.service.failure(job_id)
        self.assertEqual(len(view.evidence_refs), 1)
        self.assertEqual(view.evidence[0]["artifact_id"], view.evidence_refs[0])

    def test_failure_view_never_exposes_raw_source(self):
        job_id = self.malformed()
        self.service.run_once()
        view = self.service.failure(job_id)
        serialized = json.dumps(view.to_safe_dict(), sort_keys=True)
        self.assertFalse(view.raw_source_exposed)
        self.assertNotIn("%PDF-1.7", serialized)

    def test_failure_payload_has_governed_code(self):
        job_id = self.malformed()
        self.service.run_once()
        payload = self.service.failure(job_id).evidence[0]["payload"]
        self.assertEqual(payload["diagnostic_code"], "pdf_inspection_failed")
        self.assertEqual(payload["status"], "FAILED")

    def test_unexpected_failure_hides_secret_exception(self):
        job_id = self.create(key="transient").job_id
        with patch.object(native_jobs, "inspect_real_pdf_toc", side_effect=RuntimeError("TOP_SECRET_DETAIL")):
            self.service.run_once()
        serialized = json.dumps(self.service.failure(job_id).to_safe_dict(), sort_keys=True)
        self.assertIn("internal_worker_error", serialized)
        self.assertNotIn("TOP_SECRET_DETAIL", serialized)

    def test_failure_view_survives_restart(self):
        job_id = self.malformed()
        self.service.run_once()
        before = self.service.failure(job_id).to_safe_dict()
        self.service.close()
        from bie.app_product.service import OperatorService
        self.service = OperatorService(self.root)
        self.assertEqual(self.service.failure(job_id).to_safe_dict(), before)


if __name__ == "__main__":
    import unittest
    unittest.main()
