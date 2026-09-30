from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from apps.api.job_service import JobNotFound, PdfInspectionJobService
from bie.infrastructure.artifact_store import BlobRef
from bie.infrastructure.durable_task_queue import DurableQueueError

from .contracts import (
    ControlConflict,
    ControlReceipt,
    FailureView,
    InvalidSource,
    ProjectionError,
    RunTimeline,
    RunView,
)
from .operator_store import OperatorStore
from .source_validation import validate_source


_DENIED_EVIDENCE_KEYS = {"text", "raw_text", "content", "source_bytes", "pdf_bytes"}


def _safe_json(value: Any, *, depth: int = 0) -> Any:
    if depth > 8:
        raise ProjectionError("evidence_nesting_too_deep")
    if value is None or type(value) in {bool, int, float, str}:
        if type(value) is str and len(value) > 4096:
            raise ProjectionError("evidence_string_too_large")
        return value
    if type(value) is list:
        if len(value) > 4096:
            raise ProjectionError("evidence_list_too_large")
        return [_safe_json(v, depth=depth + 1) for v in value]
    if type(value) is dict:
        if len(value) > 1024:
            raise ProjectionError("evidence_object_too_large")
        result = {}
        for key, item in value.items():
            if type(key) is not str or key.lower() in _DENIED_EVIDENCE_KEYS:
                raise ProjectionError("unsafe_evidence_field")
            result[key] = _safe_json(item, depth=depth + 1)
        return result
    raise ProjectionError("unsupported_evidence_value")


class OperatorService:
    """Product/operator facade over the existing canonical PDF job service.

    It intentionally does not create a parallel engine or task queue.
    """

    def __init__(self, data_root: Path):
        self.data_root = Path(data_root)
        self.native = PdfInspectionJobService(self.data_root)
        self.operator = OperatorStore(self.data_root / "section18_operator.sqlite3")

    def close(self):
        self.native.close()

    @staticmethod
    def _task_id(job_id: str) -> str:
        if not job_id.startswith("job-") or len(job_id) != 68:
            raise ProjectionError("invalid_job_id")
        return "inspect-" + job_id[4:]

    def source_validation(self, payload: bytes, display_name: str | None, media_type: str = "application/pdf"):
        return validate_source(payload, display_name, media_type)

    def create_run(
        self,
        payload: bytes,
        idempotency_key: str,
        display_name: str | None = None,
        media_type: str = "application/pdf",
    ) -> RunView:
        validation = validate_source(payload, display_name, media_type)
        if validation.status != "READY_TO_SUBMIT":
            raise InvalidSource("source_rejected", validation)
        job = self.native.submit(payload, idempotency_key)
        self.operator.remember_source(
            job["job_id"],
            validation.display_name,
            validation.source_sha256 or "",
            validation.byte_length,
            validation.media_type,
        )
        return self.status(job["job_id"])

    def status(self, job_id: str) -> RunView:
        native = self.native.status(job_id)
        control = self.operator.control_state(job_id)
        visible_status = native["status"]
        if control == "PAUSED":
            visible_status = "PAUSED"
        elif control == "CANCELLED":
            visible_status = "CANCELLED"
        return RunView(
            job_id,
            visible_status,
            native["status"],
            native["queue_state"],
            native["source_hash"],
            bool(native["result_available"]),
            control,
        )

    def timeline(self, job_id: str) -> RunTimeline:
        state = self.native.persistence.load_run_state(job_id)
        task_id = self._task_id(job_id)
        try:
            queue_events = tuple(self.native.queue.events(task_id))
        except DurableQueueError as exc:
            raise ProjectionError("queue_timeline_unavailable") from exc
        stage_events = tuple(dict(event) for event in state["events"])
        control_events = self.operator.events(job_id)
        return RunTimeline(job_id, stage_events, queue_events, control_events)

    def failure(self, job_id: str) -> FailureView:
        state = self.native.persistence.load_run_state(job_id)
        stage = state["stages"].get("PDF_INSPECTION")
        if not stage or not stage["attempts"]:
            raise ProjectionError("failure_stage_missing")
        attempt = stage["attempts"][-1]
        if attempt["state"] != "FAILED":
            raise ProjectionError("run_not_failed")
        evidence = []
        for ref in attempt["evidence_refs"]:
            record = self.native.persistence.load_artifact(ref)
            if not record.evidence or record.artifact_type == "document.source.pdf":
                raise ProjectionError("unsafe_failure_evidence")
            if record.blob_size > 1024 * 1024:
                raise ProjectionError("failure_evidence_too_large")
            raw = self.native.cas.get_bytes(
                BlobRef(record.blob_algorithm, record.blob_digest, record.blob_size)
            )
            try:
                decoded = json.loads(raw.decode("utf-8"))
            except Exception as exc:
                raise ProjectionError("failure_evidence_not_safe_json") from exc
            evidence.append(
                {
                    "artifact_id": record.artifact_id,
                    "artifact_type": record.artifact_type,
                    "metadata": _safe_json(record.metadata),
                    "payload": _safe_json(decoded),
                }
            )
        return FailureView(
            job_id,
            "FAILED",
            tuple(attempt["diagnostics"]),
            tuple(attempt["evidence_refs"]),
            tuple(evidence),
            False,
        )

    def retry(self, job_id: str, reason: str = "operator_retry") -> ControlReceipt:
        view = self.status(job_id)
        if view.control_state == "CANCELLED":
            raise ControlConflict("cancelled_run_cannot_retry")
        if view.canonical_status != "FAILED":
            raise ControlConflict("retry_requires_failed_run")
        failed_delivery = self.native.queue.get(self._task_id(job_id))
        if failed_delivery.state != "DEAD_LETTER":
            raise ControlConflict("retry_requires_dead_letter")

        previous = self.operator.retries(job_id)
        if previous:
            latest_child = previous[-1]["child_job_id"]
            try:
                latest_status = self.native.status(latest_child)
            except JobNotFound as exc:
                raise ProjectionError("retry_lineage_child_missing") from exc
            if latest_status["status"] in {"READY", "RUNNING", "SUCCEEDED"}:
                raise ControlConflict("retry_already_active_or_completed")

        state = self.native.persistence.load_run_state(job_id)
        attempt = state["stages"]["PDF_INSPECTION"]["attempts"][-1]
        source_id = attempt["input_artifact_refs"][0]
        record = self.native.persistence.load_artifact(source_id)
        if record.artifact_type != "document.source.pdf":
            raise ProjectionError("retry_source_artifact_type_mismatch")
        source_bytes = self.native.cas.get_bytes(
            BlobRef(record.blob_algorithm, record.blob_digest, record.blob_size)
        )
        source_meta = self.operator.source(job_id)
        if source_meta is None or source_meta["source_hash"] != record.metadata.get("source_hash"):
            raise ProjectionError("retry_source_index_binding_missing")

        retry_no = len(previous) + 1
        retry_key = f"section18-retry-{job_id[4:]}-{retry_no}"
        child = self.native.submit(source_bytes, retry_key)
        child_id = child["job_id"]
        self.operator.remember_source(
            child_id,
            str(source_meta["display_name"]),
            str(source_meta["source_hash"]),
            int(source_meta["byte_length"]),
            str(source_meta["media_type"]),
        )
        self.operator.record_retry(job_id, child_id, reason)
        child_view = self.status(child_id)
        return ControlReceipt(
            job_id, "RETRY", "RETRY_QUEUED", child_view.queue_state, reason, child_id
        )

    def pause(self, job_id: str, reason: str = "operator_pause") -> ControlReceipt:
        view = self.status(job_id)
        if view.control_state == "PAUSED":
            return ControlReceipt(job_id, "PAUSE", "PAUSED", view.queue_state, reason)
        if view.control_state == "CANCELLED":
            raise ControlConflict("cancelled_run_cannot_pause")
        delivery = self.native.queue.get(self._task_id(job_id))
        if delivery.state != "READY":
            raise ControlConflict("pause_only_supported_before_worker_claim")
        self.native.queue.dead_letter(delivery.task.task_id, "operator_pause")
        self.operator.transition(job_id, "PAUSED", action="PAUSE", reason=reason)
        return ControlReceipt(job_id, "PAUSE", "PAUSED", "DEAD_LETTER", reason)

    def resume(self, job_id: str, reason: str = "operator_resume") -> ControlReceipt:
        if self.operator.control_state(job_id) != "PAUSED":
            raise ControlConflict("resume_requires_paused_run")
        delivery = self.native.queue.get(self._task_id(job_id))
        if delivery.state != "DEAD_LETTER" or delivery.last_reason != "operator_pause":
            raise ControlConflict("paused_queue_binding_lost")
        self.native.queue.redrive(delivery.task.task_id)
        self.operator.transition(job_id, "ACTIVE", action="RESUME", reason=reason)
        return ControlReceipt(job_id, "RESUME", "ACTIVE", "READY", reason)

    def cancel(self, job_id: str, reason: str = "operator_cancel") -> ControlReceipt:
        view = self.status(job_id)
        if view.control_state == "CANCELLED":
            return ControlReceipt(job_id, "CANCEL", "CANCELLED", view.queue_state, reason)
        delivery = self.native.queue.get(self._task_id(job_id))
        if delivery.state in {"DELIVERED", "ACKED"}:
            raise ControlConflict("cancel_not_safe_after_worker_claim")
        if view.canonical_status in {"SUCCEEDED", "FAILED"}:
            raise ControlConflict("terminal_run_cannot_cancel")
        self.native.queue.dead_letter(delivery.task.task_id, "operator_cancelled")
        self.operator.transition(job_id, "CANCELLED", action="CANCEL", reason=reason)
        return ControlReceipt(job_id, "CANCEL", "CANCELLED", "DEAD_LETTER", reason)

    def run_once(self, worker_id: str = "bie-section18-local"):
        return self.native.run_once(worker_id)
