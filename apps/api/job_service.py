"""Local durable PDF inspection jobs composed from canonical BIE stores."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re

from bie.document_intelligence.real_pdf_toc_runtime import (
    RealPdfTocRuntimeError,
    inspect_real_pdf_toc,
)
from bie.infrastructure.artifact_store import BlobRef, FileSystemCAS
from bie.infrastructure.durable_task_queue import (
    DurableTaskMessage,
    SQLiteDurableTaskQueue,
)
from bie.infrastructure.idempotency_store import (
    IdempotencyError,
    SQLiteIdempotencyStore,
)
from bie.infrastructure.persistence import (
    PersistedArtifactRecord,
    PersistedAttempt,
    PersistedEvent,
    PersistenceError,
    SQLitePersistence,
)


STAGE_ID = "PDF_INSPECTION"
CAPABILITY = "pdf_inspection"
JOB_POLICY = "bie-pdf-inspection-job-v1"
KEY_PATTERN = re.compile(r"[A-Za-z0-9._:-]{1,128}\Z", re.ASCII)


class InvalidIdempotencyKey(ValueError):
    pass


class IdempotencyConflict(ValueError):
    pass


class JobNotFound(ValueError):
    pass


class ResultNotReady(ValueError):
    pass


class JobFailed(ValueError):
    pass


def data_root_from_env() -> Path:
    """Use user-local storage by default, outside the repository."""

    configured = os.environ.get("BIE_DATA_ROOT")
    return Path(configured).expanduser() if configured else Path.home() / ".bie" / "api"


def _canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _digest_for(key: str, source_hash: str) -> str:
    identity = f"{JOB_POLICY}\0{key}\0{source_hash}".encode("utf-8")
    return hashlib.sha256(identity).hexdigest()


def validate_idempotency_key(key: str | None) -> str:
    if key is None:
        raise InvalidIdempotencyKey("idempotency_key_required")
    normalized = key.strip()
    if not KEY_PATTERN.fullmatch(normalized):
        raise InvalidIdempotencyKey("invalid_idempotency_key")
    return normalized


@dataclass(frozen=True)
class WorkerOutcome:
    outcome: str
    job_id: str | None = None
    task_id: str | None = None

    def to_safe_dict(self) -> dict[str, str]:
        result = {"outcome": self.outcome}
        if self.job_id is not None:
            result["job_id"] = self.job_id
        if self.task_id is not None:
            result["task_id"] = self.task_id
        return result


class PdfInspectionJobService:
    """A single-stage local job adapter; no cross-store transaction is claimed."""

    def __init__(self, data_root: Path | None = None):
        self.data_root = Path(data_root) if data_root is not None else data_root_from_env()
        self.data_root.mkdir(parents=True, exist_ok=True)
        self.persistence = SQLitePersistence(self.data_root / "runs.sqlite3")
        self.queue = SQLiteDurableTaskQueue(self.data_root / "queue.sqlite3")
        self.idempotency = SQLiteIdempotencyStore(str(self.data_root / "idempotency.sqlite3"))
        self.cas = FileSystemCAS(self.data_root / "cas")

    def close(self) -> None:
        self.idempotency.close()

    @staticmethod
    def _ids(digest: str) -> tuple[str, str, str, str, str]:
        return (
            f"job-{digest}",
            f"inspect-{digest}",
            f"source-{digest}",
            f"result-{digest}",
            f"evidence-{digest}",
        )

    def _load_run(self, job_id: str) -> dict[str, object] | None:
        try:
            return self.persistence.load_run_state(job_id)
        except PersistenceError as exc:
            if str(exc) == "run not found":
                return None
            raise

    def _register_blob(
        self,
        artifact_id: str,
        artifact_type: str,
        data: bytes,
        job_id: str,
        *,
        evidence: bool = False,
        metadata: dict[str, object] | None = None,
        parents: list[str] | None = None,
    ) -> PersistedArtifactRecord:
        ref = self.cas.put_bytes(data)
        record = PersistedArtifactRecord(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            blob_algorithm=ref.algorithm,
            blob_digest=ref.digest,
            blob_size=ref.size,
            run_id=job_id,
            stage_id=STAGE_ID,
            evidence=evidence,
            metadata=dict(metadata or {}),
            parent_artifact_ids=list(parents or []),
        )
        self.persistence.register_artifact(record)
        return record

    def _transition(
        self,
        job_id: str,
        from_state: str,
        to_state: str,
        *,
        input_refs: list[str] | None = None,
        output_refs: list[str] | None = None,
        evidence_refs: list[str] | None = None,
        diagnostics: list[str] | None = None,
        reason: str,
    ) -> None:
        self.persistence.save_attempt(
            job_id,
            PersistedAttempt(
                STAGE_ID,
                1,
                to_state,
                input_artifact_refs=list(input_refs or []),
                output_artifact_refs=list(output_refs or []),
                evidence_refs=list(evidence_refs or []),
                diagnostics=list(diagnostics or []),
            ),
        )
        self.persistence.append_event(
            job_id,
            PersistedEvent(
                0, STAGE_ID, from_state, to_state, 1, _timestamp(), reason,
                list(evidence_refs or []),
            ),
        )

    def submit(self, pdf_bytes: bytes, idempotency_key: str) -> dict[str, object]:
        key = validate_idempotency_key(idempotency_key)
        source_hash = hashlib.sha256(pdf_bytes).hexdigest()
        digest = _digest_for(key, source_hash)
        job_id, task_id, source_id, _, _ = self._ids(digest)
        try:
            self.idempotency.claim(key, source_hash, job_id)
        except IdempotencyError as exc:
            if "fingerprint conflict" in str(exc):
                raise IdempotencyConflict("idempotency_conflict") from exc
            raise

        # Each step can safely be repeated after a process interruption.
        run = self._load_run(job_id)
        if run is None:
            self.persistence.create_run(job_id, {STAGE_ID: []})
        self._register_blob(
            source_id, "document.source.pdf", pdf_bytes, job_id,
            metadata={"source_hash": source_hash, "byte_length": len(pdf_bytes),
                      "media_type": "application/pdf"},
        )
        run = self.persistence.load_run_state(job_id)
        attempt = run["stages"][STAGE_ID]["attempts"][0]
        if attempt["state"] == "PENDING":
            self._transition(job_id, "PENDING", "READY", input_refs=[source_id], reason="source_stored")
            self.persistence.set_run_state(job_id, "ACTIVE")
            run = self.persistence.load_run_state(job_id)
            attempt = run["stages"][STAGE_ID]["attempts"][0]
        if run["run_state"] == "CREATED":
            self.persistence.set_run_state(job_id, "ACTIVE")
        if attempt["state"] == "READY":
            self.queue.enqueue(DurableTaskMessage(
                task_id, job_id, STAGE_ID, 1, key, [CAPABILITY], [source_id],
                max_deliveries=1,
            ))
        return {
            "job_id": job_id,
            "status": attempt["state"],
            "source_hash": source_hash,
            "result_available": attempt["state"] == "SUCCEEDED",
        }

    def status(self, job_id: str) -> dict[str, object]:
        run = self._load_run(job_id)
        if run is None or STAGE_ID not in run["stages"]:
            raise JobNotFound("job_not_found")
        attempt = run["stages"][STAGE_ID]["attempts"][0]
        if attempt["state"] not in {"READY", "RUNNING", "SUCCEEDED", "FAILED"}:
            raise RuntimeError("job lifecycle is inconsistent")
        source_id = attempt["input_artifact_refs"][0]
        source = self.persistence.load_artifact(source_id)
        digest = job_id.removeprefix("job-")
        queue_state = self.queue.get(f"inspect-{digest}").state
        return {
            "job_id": job_id,
            "status": attempt["state"],
            "source_hash": source.metadata["source_hash"],
            "result_available": attempt["state"] == "SUCCEEDED",
            "queue_state": queue_state,
        }

    def result(self, job_id: str) -> dict[str, object]:
        status = self.status(job_id)
        if status["status"] == "FAILED":
            raise JobFailed("job_failed")
        if status["status"] != "SUCCEEDED":
            raise ResultNotReady("result_not_ready")
        result_id = f"result-{job_id.removeprefix('job-')}"
        record = self.persistence.load_artifact(result_id)
        blob = BlobRef(record.blob_algorithm, record.blob_digest, record.blob_size)
        return json.loads(self.cas.get_bytes(blob).decode("utf-8"))

    def _source_bytes(self, source_id: str) -> bytes:
        source = self.persistence.load_artifact(source_id)
        return self.cas.get_bytes(BlobRef(
            source.blob_algorithm, source.blob_digest, source.blob_size,
        ))

    def _record_failure(self, job_id: str, task_id: str, code: str) -> None:
        digest = job_id.removeprefix("job-")
        evidence_id = f"evidence-{digest}"
        run = self.persistence.load_run_state(job_id)
        attempt = run["stages"][STAGE_ID]["attempts"][0]
        source_id = attempt["input_artifact_refs"][0]
        source = self.persistence.load_artifact(source_id)
        self._register_blob(
            evidence_id, "document.inspection.evidence",
            _canonical_json({"job_id": job_id, "source_hash": source.metadata["source_hash"],
                             "status": "FAILED", "diagnostic_code": code}),
            job_id, evidence=True, parents=[source_id], metadata={"status": "FAILED"},
        )
        self._transition(
            job_id, "RUNNING", "FAILED", input_refs=[source_id],
            evidence_refs=[evidence_id], diagnostics=[code], reason=code,
        )
        self.persistence.set_run_state(job_id, "BLOCKED")
        self.queue.dead_letter(task_id, code)

    def run_once(self, worker_id: str = "bie-pdf-worker-local") -> WorkerOutcome:
        delivery = self.queue.poll(worker_id, capability_tags=[CAPABILITY])
        if delivery is None:
            return WorkerOutcome("IDLE")
        task = delivery.task
        job_id, task_id = task.run_id, task.task_id
        source_id = task.input_artifact_refs[0]
        try:
            self._transition(job_id, "READY", "RUNNING", input_refs=[source_id], reason="worker_started")
            self.persistence.set_run_state(job_id, "ACTIVE")
            source_bytes = self._source_bytes(source_id)
            inspection = inspect_real_pdf_toc(source_bytes)
            result_bytes = _canonical_json(inspection.to_safe_dict())
            digest = job_id.removeprefix("job-")
            result_id, evidence_id = f"result-{digest}", f"evidence-{digest}"
            result_record = self._register_blob(
                result_id, "document.inspection.safe_json", result_bytes, job_id,
                parents=[source_id], metadata={"source_hash": inspection.source_hash},
            )
            evidence = {
                "job_id": job_id,
                "source_hash": inspection.source_hash,
                "result_blob_hash": result_record.blob_digest,
                "result_byte_length": result_record.blob_size,
                "runtime_policy": inspection.toc_reconciliation_policy,
                "page_count": inspection.page_count,
                "total_blocks": inspection.total_blocks,
                "status": "SUCCEEDED",
            }
            self._register_blob(
                evidence_id, "document.inspection.evidence", _canonical_json(evidence), job_id,
                evidence=True, parents=[result_id], metadata={"status": "SUCCEEDED"},
            )
            self._transition(
                job_id, "RUNNING", "SUCCEEDED", input_refs=[source_id],
                output_refs=[result_id], evidence_refs=[evidence_id], reason="inspection_complete",
            )
            self.persistence.set_run_state(job_id, "EXECUTION_COMPLETE")
            self.queue.ack(task_id, worker_id)
            self.idempotency.complete(task.idempotency_key, job_id, result_id)
            return WorkerOutcome("ACKED", job_id, task_id)
        except Exception as exc:
            code = "pdf_inspection_failed" if isinstance(exc, RealPdfTocRuntimeError) else "internal_worker_error"
            self._record_failure(job_id, task_id, code)
            return WorkerOutcome("FAILED", job_id, task_id)
