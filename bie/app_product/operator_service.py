from __future__ import annotations

from datetime import datetime, timezone
import json

from apps.api import job_service as jobs_module
from apps.api.job_service import (
    CAPABILITY,
    STAGE_ID,
    PdfInspectionJobService,
    WorkerOutcome,
)
from bie.document_intelligence.real_pdf_toc_runtime import RealPdfTocRuntimeError
from bie.infrastructure.artifact_store import BlobRef
from bie.infrastructure.durable_task_queue import DurableQueueError, DurableTaskMessage
from bie.infrastructure.persistence import PersistedAttempt, PersistedEvent, PersistenceError

from .control_store import RunControlError, RunControlStore


class OperatorConflict(ValueError):
    pass


class OperatorJobService(PdfInspectionJobService):
    """Operator-safe view/control adapter over the canonical local job stores.

    Execution state, task delivery, source/result/evidence bytes and idempotency
    remain in the existing BIE stores inherited from PdfInspectionJobService.
    The additional SQLite file stores only operator control intent/events.
    """

    def __init__(self, data_root=None):
        super().__init__(data_root)
        self.controls = RunControlStore(self.data_root / "operator_controls.sqlite3")

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _task_id(job_id: str, attempt: int) -> str:
        digest = job_id.removeprefix("job-")
        return f"inspect-{digest}" if attempt == 1 else f"inspect-{digest}-attempt-{attempt}"

    @staticmethod
    def _evidence_id(job_id: str, attempt: int, suffix: str = "") -> str:
        digest = job_id.removeprefix("job-")
        if attempt == 1 and not suffix:
            return f"evidence-{digest}"
        tail = f"-{suffix}" if suffix else ""
        return f"evidence-{digest}-attempt-{attempt}{tail}"

    def submit(self, pdf_bytes: bytes, idempotency_key: str) -> dict[str, object]:
        result = super().submit(pdf_bytes, idempotency_key)
        self.controls.ensure_active(str(result["job_id"]))
        return self.status(str(result["job_id"]))

    def _run(self, job_id: str) -> dict[str, object]:
        run = self._load_run(job_id)
        if run is None or STAGE_ID not in run["stages"]:
            raise OperatorConflict("job_not_found")
        attempts = run["stages"][STAGE_ID]["attempts"]
        if not attempts:
            raise OperatorConflict("job_attempt_missing")
        return run

    def _attempt(self, job_id: str, attempt_number: int | None = None) -> dict[str, object]:
        run = self._run(job_id)
        attempts = run["stages"][STAGE_ID]["attempts"]
        if attempt_number is None:
            return attempts[-1]
        for attempt in attempts:
            if int(attempt["attempt"]) == attempt_number:
                return attempt
        raise OperatorConflict("job_attempt_missing")

    def _queue_state(self, job_id: str, attempt: int) -> str:
        try:
            return self.queue.get(self._task_id(job_id, attempt)).state
        except DurableQueueError:
            return "MISSING"

    def status(self, job_id: str) -> dict[str, object]:
        run = self._run(job_id)
        attempt = run["stages"][STAGE_ID]["attempts"][-1]
        attempt_number = int(attempt["attempt"])
        if not attempt["input_artifact_refs"]:
            raise OperatorConflict("job_source_missing")
        source = self.persistence.load_artifact(attempt["input_artifact_refs"][0])
        control = self.controls.ensure_active(job_id)
        canonical = str(attempt["state"])
        effective = canonical
        if canonical in {"PENDING", "READY", "RUNNING"}:
            if control.state == "PAUSED":
                effective = "PAUSED"
            elif control.state == "CANCEL_REQUESTED":
                effective = "CANCEL_REQUESTED"
            elif control.state == "CANCELLED":
                effective = "CANCELLED"
        elif canonical == "BLOCKED" and control.state == "CANCELLED":
            effective = "CANCELLED"
        return {
            "schema_version": "bie.app.run-status/1",
            "job_id": job_id,
            "status": effective,
            "canonical_status": canonical,
            "run_state": run["run_state"],
            "attempt": attempt_number,
            "source_hash": source.metadata["source_hash"],
            "result_available": canonical == "SUCCEEDED",
            "queue_state": self._queue_state(job_id, attempt_number),
            "control_state": control.state,
            "control_revision": control.revision,
            "product_accepted": False,
        }

    def timeline(self, job_id: str) -> dict[str, object]:
        run = self._run(job_id)
        rows: list[dict[str, object]] = []
        for event in run["events"]:
            rows.append({
                "event_kind": "stage",
                "event_id": f"stage:{event['sequence']}",
                "timestamp": event["timestamp"],
                "stage_id": event["stage_id"],
                "from_state": event["from_state"],
                "to_state": event["to_state"],
                "attempt": event["attempt"],
                "reason": event["reason"],
                "evidence_refs": list(event["evidence_refs"]),
            })
        for event in self.controls.events(job_id):
            rows.append({
                "event_kind": "control",
                "event_id": f"control:{event['sequence']}",
                "timestamp": event["observed_at"],
                "stage_id": STAGE_ID,
                "from_state": event["from_state"],
                "to_state": event["to_state"],
                "attempt": self.status(job_id)["attempt"],
                "reason": event["reason"],
                "evidence_refs": [],
            })
        rows.sort(key=lambda row: (str(row["timestamp"]), str(row["event_id"])))
        return {
            "schema_version": "bie.app.stage-timeline/1",
            "job_id": job_id,
            "run_state": run["run_state"],
            "events": rows,
            "event_count": len(rows),
            "product_accepted": False,
        }

    def failure_view(self, job_id: str) -> dict[str, object]:
        attempt = self._attempt(job_id)
        canonical = str(attempt["state"])
        status = self.status(job_id)
        available = canonical in {"FAILED", "BLOCKED"}
        return {
            "schema_version": "bie.app.failure-view/1",
            "job_id": job_id,
            "failure_available": available,
            "status": status["status"],
            "canonical_status": canonical,
            "attempt": int(attempt["attempt"]),
            "diagnostic_codes": list(attempt["diagnostics"]) if available else [],
            "evidence_refs": list(attempt["evidence_refs"]) if available else [],
            "retryable": (
                canonical == "FAILED"
                and status["queue_state"] == "DEAD_LETTER"
                and status["control_state"] == "ACTIVE"
            ),
            "raw_exception_exposed": False,
            "product_accepted": False,
        }

    def _transition_attempt(
        self,
        job_id: str,
        attempt_number: int,
        from_state: str,
        to_state: str,
        *,
        input_refs=None,
        output_refs=None,
        evidence_refs=None,
        diagnostics=None,
        reason: str,
    ) -> None:
        current = self._attempt(job_id, attempt_number)
        if current["state"] != from_state:
            raise OperatorConflict("stale_stage_transition")
        self.persistence.save_attempt(
            job_id,
            PersistedAttempt(
                STAGE_ID,
                attempt_number,
                to_state,
                input_artifact_refs=list(input_refs or current["input_artifact_refs"]),
                output_artifact_refs=list(output_refs or []),
                evidence_refs=list(evidence_refs or []),
                diagnostics=list(diagnostics or []),
            ),
        )
        self.persistence.append_event(
            job_id,
            PersistedEvent(
                0,
                STAGE_ID,
                from_state,
                to_state,
                attempt_number,
                self._now(),
                reason,
                list(evidence_refs or []),
            ),
        )

    def pause(self, job_id: str) -> dict[str, object]:
        status = self.status(job_id)
        if status["canonical_status"] != "READY" or status["queue_state"] != "READY":
            raise OperatorConflict("pause_requires_ready_job")
        if status["control_state"] != "ACTIVE":
            raise OperatorConflict("pause_requires_active_control")
        self.controls.transition(job_id, "PAUSED", "operator_pause")
        return self.status(job_id)

    def resume(self, job_id: str) -> dict[str, object]:
        status = self.status(job_id)
        if status["canonical_status"] != "READY":
            raise OperatorConflict("resume_requires_ready_job")
        if status["control_state"] != "PAUSED":
            raise OperatorConflict("resume_requires_paused_control")
        self.controls.transition(job_id, "ACTIVE", "operator_resume")
        return self.status(job_id)

    def cancel(self, job_id: str) -> dict[str, object]:
        status = self.status(job_id)
        if status["canonical_status"] not in {"READY", "RUNNING"}:
            raise OperatorConflict("cancel_requires_active_job")
        if status["control_state"] not in {"ACTIVE", "PAUSED", "CANCEL_REQUESTED"}:
            raise OperatorConflict("cancel_control_conflict")
        if status["control_state"] != "CANCEL_REQUESTED":
            self.controls.transition(job_id, "CANCEL_REQUESTED", "operator_cancel_request")
        if status["canonical_status"] == "READY" and status["queue_state"] == "READY":
            self._finalize_cancel(job_id, int(status["attempt"]), self._task_id(job_id, int(status["attempt"])))
        return self.status(job_id)

    def retry(self, job_id: str) -> dict[str, object]:
        run = self._run(job_id)
        previous = run["stages"][STAGE_ID]["attempts"][-1]
        if previous["state"] != "FAILED":
            raise OperatorConflict("retry_requires_failed_job")
        control = self.controls.get(job_id)
        if control.state != "ACTIVE":
            raise OperatorConflict("retry_control_conflict")
        previous_number = int(previous["attempt"])
        old_task = self.queue.get(self._task_id(job_id, previous_number))
        if old_task.state != "DEAD_LETTER":
            raise OperatorConflict("retry_requires_dead_letter")
        next_number = previous_number + 1
        refs = list(previous["input_artifact_refs"])
        if len(refs) != 1:
            raise OperatorConflict("retry_source_invalid")
        self.persistence.save_attempt(
            job_id,
            PersistedAttempt(
                STAGE_ID,
                next_number,
                "READY",
                input_artifact_refs=refs,
            ),
        )
        self.persistence.append_event(
            job_id,
            PersistedEvent(
                0,
                STAGE_ID,
                "FAILED",
                "READY",
                next_number,
                self._now(),
                "operator_retry",
                [],
            ),
        )
        self.persistence.set_run_state(job_id, "ACTIVE")
        task_id = self._task_id(job_id, next_number)
        self.queue.enqueue(
            DurableTaskMessage(
                task_id,
                job_id,
                STAGE_ID,
                next_number,
                old_task.task.idempotency_key,
                list(old_task.task.required_capability_tags),
                refs,
                priority=old_task.task.priority,
                max_deliveries=old_task.task.max_deliveries,
            )
        )
        return self.status(job_id)

    def _record_failure_attempt(
        self,
        job_id: str,
        task_id: str,
        attempt_number: int,
        code: str,
    ) -> None:
        attempt = self._attempt(job_id, attempt_number)
        source_id = attempt["input_artifact_refs"][0]
        source = self.persistence.load_artifact(source_id)
        evidence_id = self._evidence_id(job_id, attempt_number)
        self._register_blob(
            evidence_id,
            "document.inspection.evidence",
            jobs_module._canonical_json({
                "job_id": job_id,
                "attempt": attempt_number,
                "source_hash": source.metadata["source_hash"],
                "status": "FAILED",
                "diagnostic_code": code,
            }),
            job_id,
            evidence=True,
            parents=[source_id],
            metadata={"status": "FAILED", "attempt": attempt_number},
        )
        self._transition_attempt(
            job_id,
            attempt_number,
            "RUNNING",
            "FAILED",
            input_refs=[source_id],
            evidence_refs=[evidence_id],
            diagnostics=[code],
            reason=code,
        )
        self.persistence.set_run_state(job_id, "BLOCKED")
        self.queue.dead_letter(task_id, code)

    def _finalize_cancel(self, job_id: str, attempt_number: int, task_id: str) -> None:
        attempt = self._attempt(job_id, attempt_number)
        if attempt["state"] not in {"READY", "RUNNING"}:
            raise OperatorConflict("cancel_stage_conflict")
        source_id = attempt["input_artifact_refs"][0]
        source = self.persistence.load_artifact(source_id)
        evidence_id = self._evidence_id(job_id, attempt_number, "cancel")
        self._register_blob(
            evidence_id,
            "operator.cancellation.evidence",
            jobs_module._canonical_json({
                "job_id": job_id,
                "attempt": attempt_number,
                "source_hash": source.metadata["source_hash"],
                "status": "CANCELLED",
                "diagnostic_code": "cancelled_by_operator",
            }),
            job_id,
            evidence=True,
            parents=[source_id],
            metadata={"status": "CANCELLED", "attempt": attempt_number},
        )
        from_state = str(attempt["state"])
        self._transition_attempt(
            job_id,
            attempt_number,
            from_state,
            "BLOCKED",
            input_refs=[source_id],
            evidence_refs=[evidence_id],
            diagnostics=["cancelled_by_operator"],
            reason="cancelled_by_operator",
        )
        self.persistence.set_run_state(job_id, "BLOCKED")
        try:
            queue_state = self.queue.get(task_id).state
            if queue_state not in {"ACKED", "DEAD_LETTER"}:
                self.queue.dead_letter(task_id, "cancelled_by_operator")
        except DurableQueueError:
            pass
        control = self.controls.get(job_id)
        if control.state == "CANCEL_REQUESTED":
            self.controls.transition(job_id, "CANCELLED", "operator_cancel_acknowledged")

    def run_once(self, worker_id: str = "bie-operator-worker-local") -> WorkerOutcome:
        delivery = self.queue.poll(worker_id, capability_tags=[CAPABILITY])
        if delivery is None:
            return WorkerOutcome("IDLE")
        task = delivery.task
        job_id, task_id, attempt_number = task.run_id, task.task_id, int(task.attempt)
        source_id = task.input_artifact_refs[0]
        control = self.controls.ensure_active(job_id)

        if control.state == "PAUSED":
            self.queue.nack(task_id, worker_id, delay_seconds=1.0, reason="paused_by_operator")
            return WorkerOutcome("PAUSED", job_id, task_id)
        if control.state in {"CANCEL_REQUESTED", "CANCELLED"}:
            self._finalize_cancel(job_id, attempt_number, task_id)
            return WorkerOutcome("CANCELLED", job_id, task_id)

        try:
            self._transition_attempt(
                job_id,
                attempt_number,
                "READY",
                "RUNNING",
                input_refs=[source_id],
                reason="worker_started",
            )
            self.persistence.set_run_state(job_id, "ACTIVE")
            source_bytes = self._source_bytes(source_id)
            inspection = jobs_module.inspect_real_pdf_toc(source_bytes)

            if self.controls.get(job_id).state == "CANCEL_REQUESTED":
                self._finalize_cancel(job_id, attempt_number, task_id)
                return WorkerOutcome("CANCELLED", job_id, task_id)

            result_bytes = jobs_module._canonical_json(inspection.to_safe_dict())
            digest = job_id.removeprefix("job-")
            result_id = f"result-{digest}"
            evidence_id = self._evidence_id(job_id, attempt_number)
            result_record = self._register_blob(
                result_id,
                "document.inspection.safe_json",
                result_bytes,
                job_id,
                parents=[source_id],
                metadata={"source_hash": inspection.source_hash},
            )
            evidence = {
                "job_id": job_id,
                "attempt": attempt_number,
                "source_hash": inspection.source_hash,
                "result_blob_hash": result_record.blob_digest,
                "result_byte_length": result_record.blob_size,
                "runtime_policy": inspection.toc_reconciliation_policy,
                "page_count": inspection.page_count,
                "total_blocks": inspection.total_blocks,
                "status": "SUCCEEDED",
            }
            self._register_blob(
                evidence_id,
                "document.inspection.evidence",
                jobs_module._canonical_json(evidence),
                job_id,
                evidence=True,
                parents=[result_id],
                metadata={"status": "SUCCEEDED", "attempt": attempt_number},
            )
            self._transition_attempt(
                job_id,
                attempt_number,
                "RUNNING",
                "SUCCEEDED",
                input_refs=[source_id],
                output_refs=[result_id],
                evidence_refs=[evidence_id],
                reason="inspection_complete",
            )
            self.persistence.set_run_state(job_id, "EXECUTION_COMPLETE")
            self.queue.ack(task_id, worker_id)
            self.idempotency.complete(task.idempotency_key, job_id, result_id)
            return WorkerOutcome("ACKED", job_id, task_id)
        except Exception as exc:
            try:
                current = self._attempt(job_id, attempt_number)
                if current["state"] == "RUNNING":
                    code = (
                        "pdf_inspection_failed"
                        if isinstance(exc, RealPdfTocRuntimeError)
                        else "internal_worker_error"
                    )
                    self._record_failure_attempt(job_id, task_id, attempt_number, code)
            except Exception:
                pass
            return WorkerOutcome("FAILED", job_id, task_id)
