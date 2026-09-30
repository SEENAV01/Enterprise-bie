from __future__ import annotations

from .context import OperatorContext
from .models import OperatorConflict


def _task_id(canonical_job_id: str) -> str:
    return "inspect-" + canonical_job_id.removeprefix("job-")


class RunControlService:
    """Real controls over the existing durable queue.

    READY jobs can be paused/cancelled safely because they have not been
    delivered. In-flight cancellation is intentionally blocked rather than
    pretending that a running worker was stopped.
    """

    def __init__(self, context: OperatorContext):
        self.context = context

    def pause(self, run_id: str) -> dict[str, object]:
        run = self.context.operator.get_run(run_id)
        if run.state != "READY" or run.canonical_job_id is None:
            raise OperatorConflict("pause_requires_ready_run")
        service = self.context.job_service()
        try:
            task_id = _task_id(run.canonical_job_id)
            delivery = service.queue.get(task_id)
            if delivery.state != "READY":
                raise OperatorConflict("pause_requires_undelivered_task")
            service.queue.dead_letter(task_id, "operator_pause")
        finally:
            service.close()
        updated = self.context.operator.transition(
            run_id,
            expected={"READY"},
            target="PAUSED",
            event_type="RUN_PAUSED",
            payload={"task_id": task_id},
        )
        return updated.to_safe_dict()

    def resume(self, run_id: str) -> dict[str, object]:
        run = self.context.operator.get_run(run_id)
        if run.state != "PAUSED" or run.canonical_job_id is None:
            raise OperatorConflict("resume_requires_paused_run")
        service = self.context.job_service()
        try:
            task_id = _task_id(run.canonical_job_id)
            delivery = service.queue.get(task_id)
            if delivery.state != "DEAD_LETTER" or delivery.last_reason != "operator_pause":
                raise OperatorConflict("pause_queue_state_mismatch")
            service.queue.redrive(task_id)
        finally:
            service.close()
        updated = self.context.operator.transition(
            run_id,
            expected={"PAUSED"},
            target="READY",
            event_type="RUN_RESUMED",
            payload={"task_id": task_id},
        )
        return updated.to_safe_dict()

    def cancel(self, run_id: str) -> dict[str, object]:
        run = self.context.operator.get_run(run_id)
        if run.state == "DRAFT":
            return self.context.operator.transition(
                run_id,
                expected={"DRAFT"},
                target="CANCELLED",
                event_type="RUN_CANCELLED",
                payload={"phase": "draft"},
            ).to_safe_dict()
        if run.state not in {"READY", "PAUSED"} or run.canonical_job_id is None:
            raise OperatorConflict("cancel_requires_draft_or_undelivered_run")
        service = self.context.job_service()
        try:
            task_id = _task_id(run.canonical_job_id)
            delivery = service.queue.get(task_id)
            if run.state == "READY":
                if delivery.state != "READY":
                    raise OperatorConflict("in_flight_control_not_supported")
                service.queue.dead_letter(task_id, "operator_cancel")
            else:
                if delivery.state != "DEAD_LETTER" or delivery.last_reason != "operator_pause":
                    raise OperatorConflict("pause_queue_state_mismatch")
        finally:
            service.close()
        return self.context.operator.transition(
            run_id,
            expected={run.state},
            target="CANCELLED",
            event_type="RUN_CANCELLED",
            payload={"task_id": task_id},
        ).to_safe_dict()
