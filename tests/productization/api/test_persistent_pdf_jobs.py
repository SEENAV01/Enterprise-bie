"""Structural tests for the local durable PDF inspection lifecycle."""

from __future__ import annotations

import gc
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "tests" / "productization" / "document_intelligence"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(FIXTURES) not in sys.path:
    sys.path.insert(0, str(FIXTURES))

from apps.api.main import app
from apps.api.job_service import PdfInspectionJobService
import apps.api.job_service as jobs_module
from bie.document_intelligence.real_pdf_toc_runtime import inspect_real_pdf_toc
from bie.infrastructure.artifact_store import BlobRef, FileSystemCAS
from bie.infrastructure.durable_task_queue import SQLiteDurableTaskQueue
from bie.infrastructure.idempotency_store import SQLiteIdempotencyStore
from bie.infrastructure.persistence import SQLitePersistence
from structural_pdf_fixtures import hierarchy_pdf_with_outline


class PersistentPdfJobTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pdf = hierarchy_pdf_with_outline()
        cls.expected = inspect_real_pdf_toc(cls.pdf).to_safe_dict()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.env = patch.dict(os.environ, {"BIE_DATA_ROOT": str(self.root)})
        self.env.start()
        self.client = TestClient(app, raise_server_exceptions=False)

    def tearDown(self):
        self.env.stop()
        gc.collect()
        self.temp.cleanup()

    def service(self):
        return PdfInspectionJobService(self.root)

    def submit(self, *, key="structural-fixture-1", data=None):
        return self.client.post(
            "/v1/jobs/document-inspection",
            content=self.pdf if data is None else data,
            headers={"content-type": "application/pdf", "Idempotency-Key": key},
        )

    def completed(self):
        job = self.submit().json()["job"]
        service = self.service()
        try:
            outcome = service.run_once()
        finally:
            service.close()
        self.assertEqual(outcome.outcome, "ACKED")
        return job

    def test_01_uses_canonical_sqlite_persistence(self):
        service = self.service()
        self.assertIsInstance(service.persistence, SQLitePersistence)
        service.close()

    def test_02_uses_canonical_durable_queue(self):
        service = self.service()
        self.assertIsInstance(service.queue, SQLiteDurableTaskQueue)
        service.close()

    def test_03_uses_canonical_idempotency_store(self):
        service = self.service()
        self.assertIsInstance(service.idempotency, SQLiteIdempotencyStore)
        service.close()

    def test_04_uses_canonical_filesystem_cas(self):
        service = self.service()
        self.assertIsInstance(service.cas, FileSystemCAS)
        service.close()

    def test_05_submission_requires_idempotency_key(self):
        response = self.client.post(
            "/v1/jobs/document-inspection", content=self.pdf,
            headers={"content-type": "application/pdf"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "idempotency_key_required")

    def test_06_invalid_key_rejected(self):
        self.assertEqual(self.submit(key="bad key").status_code, 400)
        self.assertEqual(self.submit(key="x" * 129).json()["error"]["code"], "invalid_idempotency_key")

    def test_07_wrong_media_type_rejected(self):
        response = self.client.post(
            "/v1/jobs/document-inspection", content=self.pdf,
            headers={"content-type": "application/octet-stream", "Idempotency-Key": "k"},
        )
        self.assertEqual(response.status_code, 415)

    def test_08_empty_body_rejected(self):
        self.assertEqual(self.submit(data=b"").json()["error"]["code"], "empty_body")

    def test_09_oversize_body_rejected(self):
        import apps.api.main as api_module
        with patch.object(api_module, "MAX_PDF_BYTES", 8):
            response = self.submit(data=b"%PDF-1234")
        self.assertEqual(response.status_code, 413)

    def test_10_valid_submission_returns_202(self):
        self.assertEqual(self.submit().status_code, 202)

    def test_11_job_id_is_deterministic(self):
        first = self.submit().json()["job"]["job_id"]
        self.assertEqual(first, self.submit().json()["job"]["job_id"])
        self.assertRegex(first, r"^job-[0-9a-f]{64}$")

    def test_12_same_key_and_pdf_replays_job(self):
        self.assertEqual(self.submit().json()["job"], self.submit().json()["job"])

    def test_13_same_key_different_pdf_conflicts(self):
        self.submit()
        response = self.submit(data=b"%PDF-1.7\ndifferent")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "idempotency_conflict")

    def test_14_duplicate_submission_keeps_one_queue_item(self):
        self.submit()
        self.submit()
        service = self.service()
        self.assertEqual(service.queue.stats()["READY"], 1)
        service.close()

    def test_15_source_artifact_is_in_cas(self):
        job_id = self.submit().json()["job"]["job_id"]
        service = self.service()
        source = service.persistence.load_artifact("source-" + job_id[4:])
        self.assertEqual(service.cas.get_bytes(BlobRef(source.blob_algorithm, source.blob_digest, source.blob_size)), self.pdf)
        service.close()

    def test_16_source_metadata_has_no_text(self):
        job_id = self.submit().json()["job"]["job_id"]
        service = self.service()
        source = service.persistence.load_artifact("source-" + job_id[4:])
        self.assertEqual(source.metadata["source_hash"], hashlib.sha256(self.pdf).hexdigest())
        self.assertEqual(source.metadata["byte_length"], len(self.pdf))
        self.assertNotIn("text", json.dumps(source.metadata).lower())
        service.close()

    def test_17_initial_attempt_is_ready(self):
        job_id = self.submit().json()["job"]["job_id"]
        service = self.service()
        run = service.persistence.load_run_state(job_id)
        self.assertEqual(run["stages"]["PDF_INSPECTION"]["attempts"][0]["state"], "READY")
        service.close()

    def test_18_status_survives_restart(self):
        job_id = self.submit().json()["job"]["job_id"]
        self.assertEqual(self.client.get(f"/v1/jobs/{job_id}").json()["job"]["status"], "READY")

    def test_19_worker_polls_persisted_queue(self):
        self.submit()
        service = self.service()
        with patch.object(service.queue, "poll", wraps=service.queue.poll) as poll:
            self.assertEqual(service.run_once().outcome, "ACKED")
        poll.assert_called_once()
        service.close()

    def test_20_worker_uses_cas_integrity_read(self):
        self.submit()
        service = self.service()
        with patch.object(service.cas, "get_bytes", wraps=service.cas.get_bytes) as read:
            self.assertEqual(service.run_once().outcome, "ACKED")
        self.assertTrue(read.called)
        service.close()

    def test_21_worker_invokes_task_016_runtime(self):
        self.submit()
        service = self.service()
        with patch.object(jobs_module, "inspect_real_pdf_toc", wraps=inspect_real_pdf_toc) as inspect:
            service.run_once()
        inspect.assert_called_once_with(self.pdf)
        service.close()

    def test_22_running_state_is_persisted_before_inspection(self):
        job_id = self.submit().json()["job"]["job_id"]
        service = self.service()
        observed = []
        def inspect(data):
            observed.append(service.persistence.load_run_state(job_id)["stages"]["PDF_INSPECTION"]["attempts"][0]["state"])
            return inspect_real_pdf_toc(data)
        with patch.object(jobs_module, "inspect_real_pdf_toc", side_effect=inspect):
            service.run_once()
        self.assertEqual(observed, ["RUNNING"])
        service.close()

    def test_23_success_stores_safe_result_artifact(self):
        job_id = self.completed()["job_id"]
        service = self.service()
        result = service.persistence.load_artifact("result-" + job_id[4:])
        self.assertEqual(result.artifact_type, "document.inspection.safe_json")
        self.assertEqual(json.loads(service.cas.get_bytes(BlobRef(result.blob_algorithm, result.blob_digest, result.blob_size))), self.expected)
        service.close()

    def test_24_success_stores_safe_evidence(self):
        job_id = self.completed()["job_id"]
        service = self.service()
        self.assertEqual(len(service.persistence.evidence_for_run(job_id)), 1)
        service.close()

    def test_25_result_parents_source(self):
        job_id = self.completed()["job_id"]
        service = self.service()
        result = service.persistence.load_artifact("result-" + job_id[4:])
        self.assertEqual(result.parent_artifact_ids, ["source-" + job_id[4:]])
        service.close()

    def test_26_evidence_is_marked_evidence(self):
        job_id = self.completed()["job_id"]
        service = self.service()
        evidence = service.persistence.load_artifact("evidence-" + job_id[4:])
        self.assertTrue(evidence.evidence)
        self.assertEqual(evidence.parent_artifact_ids, ["result-" + job_id[4:]])
        service.close()

    def test_27_successful_run_is_execution_complete(self):
        job_id = self.completed()["job_id"]
        service = self.service()
        self.assertEqual(service.persistence.load_run_state(job_id)["run_state"], "EXECUTION_COMPLETE")
        service.close()

    def test_28_successful_queue_item_is_acked(self):
        job_id = self.completed()["job_id"]
        service = self.service()
        self.assertEqual(service.queue.get("inspect-" + job_id[4:]).state, "ACKED")
        service.close()

    def test_29_result_endpoint_is_exact_task_016_safe_result(self):
        job_id = self.completed()["job_id"]
        response = self.client.get(f"/v1/jobs/{job_id}/result")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["result"], self.expected)

    def test_30_result_survives_restart(self):
        job_id = self.completed()["job_id"]
        service = self.service()
        self.assertEqual(service.result(job_id), self.expected)
        service.close()

    def test_31_result_before_completion_is_409(self):
        job_id = self.submit().json()["job"]["job_id"]
        self.assertEqual(self.client.get(f"/v1/jobs/{job_id}/result").json()["error"]["code"], "result_not_ready")

    def test_32_unknown_job_is_404(self):
        self.assertEqual(self.client.get("/v1/jobs/job-missing").status_code, 404)
        self.assertEqual(self.client.get("/v1/jobs/job-missing/result").status_code, 404)

    def test_33_malformed_pdf_fails_in_worker(self):
        job_id = self.submit(data=b"%PDF-1.7\nmalformed").json()["job"]["job_id"]
        service = self.service()
        self.assertEqual(service.run_once().outcome, "FAILED")
        service.close()
        self.assertEqual(self.client.get(f"/v1/jobs/{job_id}").json()["job"]["status"], "FAILED")
        self.assertEqual(self.client.get(f"/v1/jobs/{job_id}/result").json()["error"]["code"], "job_failed")

    def test_34_governed_failure_hides_exception(self):
        job_id = self.submit(data=b"%PDF-1.7\nmalformed").json()["job"]["job_id"]
        service = self.service()
        service.run_once()
        evidence = service.persistence.load_artifact("evidence-" + job_id[4:])
        content = service.cas.get_bytes(BlobRef(evidence.blob_algorithm, evidence.blob_digest, evidence.blob_size))
        self.assertIn(b"pdf_inspection_failed", content)
        self.assertNotIn(b"Traceback", content)
        service.close()

    def test_35_unexpected_worker_failure_is_safe(self):
        job_id = self.submit().json()["job"]["job_id"]
        service = self.service()
        with patch.object(jobs_module, "inspect_real_pdf_toc", side_effect=RuntimeError("secret detail")):
            self.assertEqual(service.run_once().outcome, "FAILED")
        attempt = service.persistence.load_run_state(job_id)["stages"]["PDF_INSPECTION"]["attempts"][0]
        self.assertEqual(attempt["diagnostics"], ["internal_worker_error"])
        service.close()

    def test_36_failure_dead_letters_queue_item(self):
        job_id = self.submit(data=b"%PDF-1.7\nmalformed").json()["job"]["job_id"]
        service = self.service()
        service.run_once()
        self.assertEqual(service.queue.get("inspect-" + job_id[4:]).state, "DEAD_LETTER")
        service.close()

    def test_37_api_output_contains_no_raw_text(self):
        job_id = self.completed()["job_id"]
        output = self.client.get(f"/v1/jobs/{job_id}/result").text
        self.assertNotIn("CHAPTER 1 Foundation", output)
        self.assertNotIn("Ordinary hierarchy fixture body line one", output)

    def test_38_no_source_pdf_endpoint_exists(self):
        job_id = self.completed()["job_id"]
        self.assertEqual(self.client.get(f"/v1/jobs/{job_id}/source").status_code, 404)

    def test_39_existing_sync_inspection_works(self):
        response = self.client.post("/v1/documents/inspect", content=self.pdf, headers={"content-type": "application/pdf"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["result"], self.expected)

    def test_40_capabilities_report_local_jobs(self):
        capabilities = self.client.get("/v1/capabilities").json()
        self.assertTrue(capabilities["persistence"])
        self.assertTrue(capabilities["async_jobs"])
        self.assertFalse(capabilities["stateless"])

    def test_41_submit_restart_work_restart_result(self):
        job_id = self.submit().json()["job"]["job_id"]
        service_b = self.service()
        self.assertEqual(service_b.status(job_id)["status"], "READY")
        self.assertEqual(service_b.run_once().outcome, "ACKED")
        service_b.close()
        service_c = self.service()
        self.assertEqual(service_c.status(job_id)["status"], "SUCCEEDED")
        self.assertEqual(service_c.result(job_id), self.expected)
        service_c.close()

    def test_42_completed_replay_keeps_identity_and_queue_count(self):
        job_id = self.completed()["job_id"]
        self.assertEqual(self.submit().json()["job"]["job_id"], job_id)
        service = self.service()
        self.assertEqual(service.queue.stats()["ACKED"], 1)
        self.assertEqual(service.queue.stats()["READY"], 0)
        claim = service.idempotency.get("structural-fixture-1")
        self.assertEqual(claim.state, "COMPLETED")
        self.assertEqual(claim.result_ref, "result-" + job_id[4:])
        service.close()

    def test_43_partial_submission_replay_repairs_missing_queue(self):
        service = self.service()
        with patch.object(service.queue, "enqueue", side_effect=RuntimeError("interrupted")):
            with self.assertRaises(RuntimeError):
                service.submit(self.pdf, "recover-key")
        service.close()
        service = self.service()
        job = service.submit(self.pdf, "recover-key")
        self.assertEqual(job["status"], "READY")
        self.assertEqual(service.queue.stats()["READY"], 1)
        service.close()

    def test_44_separate_worker_process_smoke(self):
        job_id = self.submit().json()["job"]["job_id"]
        process = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "run_bie_pdf_worker.py"), "--once"],
            cwd=ROOT, env={**os.environ, "BIE_DATA_ROOT": str(self.root)},
            capture_output=True, text=True, check=False, timeout=120,
        )
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(json.loads(process.stdout)["outcome"], "ACKED")
        service = self.service()
        self.assertEqual(service.status(job_id)["status"], "SUCCEEDED")
        self.assertEqual(service.result(job_id), self.expected)
        service.close()


if __name__ == "__main__":
    unittest.main()
