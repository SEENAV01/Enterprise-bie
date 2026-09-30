from __future__ import annotations

from unittest.mock import patch

import apps.api.section18 as section18_api
from bie.app_product.contracts import MAX_SOURCE_BYTES, ProductContractError, validate_pdf_source

from tests.section18.support import Section18Case


class RunAndSourceTests(Section18Case):
    def test_001_validation_accepts_real_pdf_without_exposing_content(self):
        response = self.client.post(
            "/v1/app/sources/validate",
            content=self.pdf,
            headers={"content-type": "application/pdf"},
        )
        self.assertEqual(response.status_code, 200)
        value = response.json()
        self.assertTrue(value["valid"])
        self.assertEqual(value["issues"], [])
        self.assertEqual(len(value["source_sha256"]), 64)
        self.assertNotIn("CHAPTER", response.text)

    def test_002_validation_rejects_wrong_media_type(self):
        response = self.client.post(
            "/v1/app/sources/validate",
            content=self.pdf,
            headers={"content-type": "application/octet-stream"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["valid"])
        self.assertIn("unsupported_media_type", response.json()["issues"])

    def test_003_validation_rejects_empty_source(self):
        response = self.client.post(
            "/v1/app/sources/validate",
            content=b"",
            headers={"content-type": "application/pdf"},
        )
        self.assertFalse(response.json()["valid"])
        self.assertIn("empty_source", response.json()["issues"])

    def test_004_validation_rejects_non_pdf_signature(self):
        response = self.client.post(
            "/v1/app/sources/validate",
            content=b"not a pdf",
            headers={"content-type": "application/pdf"},
        )
        self.assertFalse(response.json()["valid"])
        self.assertIn("pdf_signature_missing", response.json()["issues"])

    def test_005_validation_reader_is_bounded(self):
        with patch.object(section18_api, "MAX_SOURCE_BYTES", 8):
            response = self.client.post(
                "/v1/app/sources/validate",
                content=b"%PDF-1234",
                headers={"content-type": "application/pdf"},
            )
        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.json()["error"]["code"], "source_too_large")

    def test_006_create_run_returns_durable_backend_identity(self):
        run = self.create()
        self.assertRegex(run["job_id"], r"^job-[0-9a-f]{64}$")
        self.assertEqual(run["canonical_status"], "READY")
        self.assertEqual(run["queue_state"], "READY")
        self.assertEqual(run["control_state"], "ACTIVE")

    def test_007_create_run_is_idempotent_for_same_key_and_source(self):
        first = self.create(key="stable-key")
        second = self.create(key="stable-key")
        self.assertEqual(first["job_id"], second["job_id"])
        self.assertEqual(first["source_hash"], second["source_hash"])

    def test_008_create_run_rejects_invalid_source_before_persistence(self):
        response = self.client.post(
            "/v1/app/runs",
            content=b"bad",
            headers={"content-type": "application/pdf", "Idempotency-Key": "bad-source"},
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["error"]["code"], "source_validation_failed")
        service = self.service()
        try:
            self.assertEqual(service.queue.stats()["READY"], 0)
        finally:
            service.close()

    def test_009_create_run_requires_idempotency_key(self):
        response = self.client.post(
            "/v1/app/runs",
            content=self.pdf,
            headers={"content-type": "application/pdf"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "idempotency_key_required")

    def test_010_same_key_different_source_conflicts(self):
        self.create(key="conflict-key")
        response = self.client.post(
            "/v1/app/runs",
            content=b"%PDF-1.7\ndifferent",
            headers={"content-type": "application/pdf", "Idempotency-Key": "conflict-key"},
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "idempotency_conflict")

    def test_011_status_survives_service_restart(self):
        run = self.create()
        response = self.client.get("/v1/app/runs/" + run["job_id"])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["job_id"], run["job_id"])
        self.assertEqual(response.json()["source_hash"], run["source_hash"])

    def test_012_source_validation_contract_rejects_non_bytes(self):
        with self.assertRaises(ProductContractError):
            validate_pdf_source("not-bytes")

    def test_013_source_validation_default_limit_is_25_mib(self):
        self.assertEqual(MAX_SOURCE_BYTES, 25 * 1024 * 1024)


if __name__ == "__main__":
    import unittest
    unittest.main()
