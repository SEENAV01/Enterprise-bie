from __future__ import annotations

import hashlib

from apps.api.job_service import IdempotencyConflict
from bie.infrastructure.artifact_store import BlobRef
from .support import AppProductCase


class CreateRunTests(AppProductCase):
    def test_create_run_uses_canonical_job_service(self):
        view = self.create()
        self.assertEqual(view.status, "READY")
        self.assertEqual(view.queue_state, "READY")

    def test_created_run_has_deterministic_identity(self):
        first = self.create().job_id
        second = self.create().job_id
        self.assertEqual(first, second)
        self.assertRegex(first, r"^job-[0-9a-f]{64}$")

    def test_run_is_in_canonical_persistence(self):
        job_id = self.create().job_id
        state = self.service.native.persistence.load_run_state(job_id)
        self.assertEqual(state["run_state"], "ACTIVE")
        self.assertIn("PDF_INSPECTION", state["stages"])

    def test_run_is_enqueued_once(self):
        self.create()
        self.create()
        stats = self.service.native.queue.stats()
        self.assertEqual(stats["READY"], 1)

    def test_source_metadata_sidecar_is_bound(self):
        view = self.create()
        row = self.service.operator.source(view.job_id)
        self.assertEqual(row["source_hash"], hashlib.sha256(self.pdf).hexdigest())
        self.assertEqual(row["display_name"], "Physics.pdf")
        self.assertEqual(row["byte_length"], len(self.pdf))

    def test_source_bytes_remain_in_canonical_cas(self):
        view = self.create()
        artifact = self.service.native.persistence.load_artifact("source-" + view.job_id[4:])
        raw = self.service.native.cas.get_bytes(
            BlobRef(artifact.blob_algorithm, artifact.blob_digest, artifact.blob_size)
        )
        self.assertEqual(raw, self.pdf)

    def test_same_key_different_source_conflicts(self):
        self.create(key="same-key")
        with self.assertRaises(IdempotencyConflict):
            self.service.create_run(b"%PDF-1.7\ndifferent", "same-key", "Other.pdf")

    def test_restart_reads_same_created_run(self):
        view = self.create()
        self.service.close()
        from bie.app_product.service import OperatorService
        self.service = OperatorService(self.root)
        self.assertEqual(self.service.status(view.job_id).to_safe_dict(), view.to_safe_dict())

    def test_create_does_not_claim_success(self):
        view = self.create()
        self.assertFalse(view.result_available)
        self.assertNotEqual(view.status, "SUCCEEDED")

    def test_control_state_starts_active(self):
        view = self.create()
        self.assertEqual(view.control_state, "ACTIVE")


if __name__ == "__main__":
    import unittest
    unittest.main()
