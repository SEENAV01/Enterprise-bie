from __future__ import annotations

import hashlib

from batch001_support import OperatorCase

from bie.infrastructure.artifact_store import ArtifactStoreError, BlobRef
from bie.product_app_v1.models import OperatorConflict
from bie.product_app_v1.retry import RetryService


class AppRun007Tests(OperatorCase):
    def _valid_source_failed_by_worker(self, key):
        result = self.imported(key)
        run_id = result["run"]["run_id"]
        import apps.api.job_service as jobs_module
        from unittest.mock import patch
        service = self.context.job_service()
        try:
            with patch.object(jobs_module, "inspect_real_pdf_toc", side_effect=RuntimeError("controlled-worker-failure")):
                self.assertEqual(service.run_once("retry-failing-worker").outcome, "FAILED")
        finally:
            service.close()
        self.assertEqual(self.observe(run_id)["state"], "FAILED")
        return run_id

    def test_retry_creates_new_canonical_attempt(self):
        run_id = self._valid_source_failed_by_worker("retry-new")
        before = self.context.operator.attempt(run_id)
        result = RetryService(self.context).retry(run_id)
        after = self.context.operator.attempt(run_id)
        self.assertEqual(after.attempt, 2)
        self.assertNotEqual(before.canonical_job_id, after.canonical_job_id)
        self.assertEqual(result["retry_of_job_id"], before.canonical_job_id)

    def test_retry_preserves_source_hash(self):
        run_id = self._valid_source_failed_by_worker("retry-hash")
        old_hash = self.context.operator.get_run(run_id).source_hash
        result = RetryService(self.context).retry(run_id)
        self.assertEqual(result["source_hash"], old_hash)
        self.assertEqual(old_hash, hashlib.sha256(self.pdf).hexdigest())

    def test_retry_preserves_failed_prior_attempt(self):
        run_id = self._valid_source_failed_by_worker("retry-history")
        prior = self.context.operator.attempt(run_id, 1)
        RetryService(self.context).retry(run_id)
        preserved = self.context.operator.attempt(run_id, 1)
        self.assertEqual(preserved.canonical_job_id, prior.canonical_job_id)
        self.assertEqual(preserved.state, "FAILED")

    def test_retry_preserves_prior_failure_evidence(self):
        run_id = self._valid_source_failed_by_worker("retry-evidence")
        prior = self.context.operator.attempt(run_id, 1)
        service = self.context.job_service()
        try:
            before = tuple(service.persistence.evidence_for_run(prior.canonical_job_id))
        finally:
            service.close()
        RetryService(self.context).retry(run_id)
        service = self.context.job_service()
        try:
            after = tuple(service.persistence.evidence_for_run(prior.canonical_job_id))
        finally:
            service.close()
        self.assertEqual(before, after)
        self.assertTrue(after)

    def test_retry_valid_source_can_succeed_on_next_attempt(self):
        run_id = self._valid_source_failed_by_worker("retry-success")
        RetryService(self.context).retry(run_id)
        self.assertEqual(self.run_native_once().outcome, "ACKED")
        self.assertEqual(self.observe(run_id)["state"], "SUCCEEDED")
        self.assertEqual(self.context.operator.get_run(run_id).attempt, 2)

    def test_retry_requires_failed_state(self):
        result = self.imported("retry-not-failed")
        with self.assertRaises(OperatorConflict):
            RetryService(self.context).retry(result["run"]["run_id"])

    def test_retry_uses_new_idempotency_key(self):
        run_id = self._valid_source_failed_by_worker("retry-key")
        prior = self.context.operator.attempt(run_id, 1)
        RetryService(self.context).retry(run_id)
        current = self.context.operator.attempt(run_id, 2)
        self.assertNotEqual(prior.idempotency_key, current.idempotency_key)
        self.assertTrue(current.idempotency_key.endswith(":attempt:2"))

    def test_retry_source_integrity_is_enforced_by_cas(self):
        run_id = self._valid_source_failed_by_worker("retry-corrupt")
        prior = self.context.operator.attempt(run_id, 1)
        service = self.context.job_service()
        try:
            source = service.persistence.load_artifact("source-" + prior.canonical_job_id[4:])
            path = service.cas._path(source.blob_digest)
            original = path.read_bytes()
            path.write_bytes(b"corrupt")
        finally:
            service.close()
        try:
            with self.assertRaises(ArtifactStoreError):
                RetryService(self.context).retry(run_id)
        finally:
            path.write_bytes(original)

    def test_retry_event_records_lineage(self):
        run_id = self._valid_source_failed_by_worker("retry-event")
        old_job = self.context.operator.attempt(run_id).canonical_job_id
        RetryService(self.context).retry(run_id)
        events = self.context.operator.events(run_id)
        retry = [e for e in events if e.event_type == "RETRY_BOUND"]
        self.assertEqual(len(retry), 1)
        self.assertEqual(retry[0].payload["retry_of_job_id"], old_job)

    def test_retry_result_does_not_claim_product_acceptance(self):
        run_id = self._valid_source_failed_by_worker("retry-claim")
        result = RetryService(self.context).retry(run_id)
        self.assertNotIn("product_accepted", result)
        self.assertNotIn("release_authorized", result)


if __name__ == "__main__":
    import unittest
    unittest.main()
