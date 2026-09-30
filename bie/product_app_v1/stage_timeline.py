from __future__ import annotations

from datetime import datetime, timezone

from .context import OperatorContext
from .models import OperatorError


def _iso_to_epoch(value: str) -> float:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except Exception as exc:
        raise OperatorError("invalid_canonical_timestamp") from exc


class StageTimelineService:
    def __init__(self, context: OperatorContext):
        self.context = context

    def timeline(self, run_id: str) -> dict[str, object]:
        run = self.context.operator.get_run(run_id)
        events: list[dict[str, object]] = []
        for event in self.context.operator.events(run_id):
            events.append({
                "origin": "operator",
                "sequence": event.sequence,
                "timestamp": event.created_at,
                "event_type": event.event_type,
                "payload": dict(event.payload),
            })
        if run.attempt > 0:
            service = self.context.job_service()
            try:
                for operator_attempt in range(1, run.attempt + 1):
                    attempt = self.context.operator.attempt(run_id, operator_attempt)
                    native = service.persistence.load_run_state(attempt.canonical_job_id)
                    for event in native["events"]:
                        events.append({
                            "origin": "canonical_persistence",
                            "sequence": int(event["sequence"]),
                            "timestamp": _iso_to_epoch(str(event["timestamp"])),
                            "event_type": "STAGE_TRANSITION",
                            "payload": {
                                "operator_attempt": operator_attempt,
                                "canonical_job_id": attempt.canonical_job_id,
                                "stage_id": event["stage_id"],
                                "from_state": event["from_state"],
                                "to_state": event["to_state"],
                                "attempt": event["attempt"],
                                "reason": event["reason"],
                                "evidence_refs": list(event["evidence_refs"]),
                            },
                        })
                    task_id = "inspect-" + attempt.canonical_job_id.removeprefix("job-")
                    for event in service.queue.events(task_id):
                        events.append({
                            "origin": "canonical_queue",
                            "sequence": int(event["sequence"]),
                            "timestamp": float(event["event_at"]),
                            "event_type": str(event["event_type"]),
                            "payload": {
                                "operator_attempt": operator_attempt,
                                "canonical_job_id": attempt.canonical_job_id,
                                "delivery_count": event["delivery_count"],
                                "reason": event["reason"],
                            },
                        })
            finally:
                service.close()
        events.sort(key=lambda row: (
            float(row["timestamp"]),
            str(row["origin"]),
            int(row["sequence"]),
        ))
        return {
            "run_id": run_id,
            "events": events,
            "event_count": len(events),
            "progress_percent": None,
            "fabricated_events": False,
        }
