from __future__ import annotations

import hashlib

from batch001_support import OperatorCase

from bie.product_app_v1.models import OperatorConflict
from bie.product_app_v1.source_import import SourceImportService


class AppRun002Tests(OperatorCase):
    def test_valid_pdf_binds_real_canonical_job(self):
        result = self.imported("valid-import")
        self.assertTrue(result["validation"]["accepted"])
        self.assertEqual(result["run"]["state"], "READY")
        self.assertRegex(result["canonical_job"]["job_id"], r"^job-[0-9a-f]{64}$")

    def test_source_hash_matches_actual_bytes(self):
        result = self.imported("hash-import")
        expected = hashlib.sha256(self.pdf).hexdigest()
        self.assertEqual(result["validation"]["sha256"], expected)
        self.assertEqual(result["run"]["source_hash"], expected)

    def test_canonical_source_artifact_contains_exact_bytes(self):
        result = self.imported("cas-import")
        job_id = result["canonical_job"]["job_id"]
        service = self.context.job_service()
        try:
            source = service.persistence.load_artifact("source-" + job_id[4:])
            from bie.infrastructure.artifact_store import BlobRef
            actual = service.cas.get_bytes(BlobRef(source.blob_algorithm, source.blob_digest, source.blob_size))
        finally:
            service.close()
        self.assertEqual(actual, self.pdf)

    def test_operator_database_does_not_store_source_bytes(self):
        result = self.imported("no-dup")
        raw = (self.root / "operator" / "section18.sqlite3").read_bytes()
        self.assertNotIn(self.pdf[:64], raw)

    def test_duplicate_initial_import_is_rejected(self):
        result = self.imported("one-import")
        with self.assertRaises(OperatorConflict):
            SourceImportService(self.context).import_pdf(
                result["run"]["run_id"], self.pdf, display_name="Again.pdf"
            )

    def test_malformed_signature_blocks_before_canonical_submit(self):
        run = self.create("bad-signature")
        result = SourceImportService(self.context).import_pdf(
            run["run_id"], b"not-a-pdf", display_name="bad.pdf"
        )
        self.assertFalse(result["validation"]["accepted"])
        self.assertEqual(result["run"]["state"], "BLOCKED")
        self.assertIsNone(result["canonical_job"])

    def test_source_name_is_safe_metadata(self):
        result = self.imported("name", name="Physics — Unit 1.pdf")
        self.assertEqual(result["run"]["source_name"], "Physics — Unit 1.pdf")

    def test_import_persists_attempt_mapping(self):
        result = self.imported("attempt")
        attempt = self.context.operator.attempt(result["run"]["run_id"])
        self.assertEqual(attempt.attempt, 1)
        self.assertEqual(attempt.canonical_job_id, result["canonical_job"]["job_id"])

    def test_import_uses_real_durable_queue(self):
        result = self.imported("queue")
        job_id = result["canonical_job"]["job_id"]
        service = self.context.job_service()
        try:
            delivery = service.queue.get("inspect-" + job_id[4:])
        finally:
            service.close()
        self.assertEqual(delivery.state, "READY")

    def test_worker_can_consume_imported_job(self):
        result = self.imported("worker")
        outcome = self.run_native_once()
        self.assertEqual(outcome.job_id, result["canonical_job"]["job_id"])
        self.assertEqual(outcome.outcome, "ACKED")


if __name__ == "__main__":
    import unittest
    unittest.main()
