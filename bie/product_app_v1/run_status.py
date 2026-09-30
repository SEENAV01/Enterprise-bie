from __future__ import annotations

from .context import OperatorContext
from .models import OperatorConflict


CANONICAL_TO_OPERATOR = {
    "READY": "READY",
    "RUNNING": "ACTIVE",
    "SUCCEEDED": "SUCCEEDED",
    "FAILED": "FAILED",
}


class RunStatusService:
    def __init__(self, context: OperatorContext):
        self.context = context

    def status(self, run_id: str) -> dict[str, object]:
        run = self.context.operator.get_run(run_id)
        base = run.to_safe_dict()
        if run.state in {"DRAFT", "PAUSED", "CANCELLED", "BLOCKED"}:
            return {
                **base,
                "canonical_status": None if run.canonical_job_id is None else "NOT_QUERIED",
                "queue_state": None,
                "result_available": run.state == "SUCCEEDED",
                "status_source": "operator_store",
            }
        if run.canonical_job_id is None:
            raise OperatorConflict("canonical_job_binding_missing")
        service = self.context.job_service()
        try:
            observed = service.status(run.canonical_job_id)
        finally:
            service.close()
        target = CANONICAL_TO_OPERATOR.get(str(observed["status"]))
        if target is None:
            raise OperatorConflict("unsupported_canonical_status")
        if target != run.state:
            run = self.context.operator.record_observation(
                run_id,
                state=target,
                event_type="CANONICAL_STATUS_OBSERVED",
                payload={
                    "canonical_status": observed["status"],
                    "queue_state": observed.get("queue_state"),
                },
            )
        return {
            **run.to_safe_dict(),
            "canonical_status": observed["status"],
            "queue_state": observed.get("queue_state"),
            "result_available": bool(observed.get("result_available")),
            "status_source": "canonical_job_service",
        }
