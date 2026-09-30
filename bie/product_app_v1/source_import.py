from __future__ import annotations

from pathlib import Path

from .context import OperatorContext
from .models import OperatorConflict, OperatorError, require_token
from .source_validation import validate_pdf_source


def _attempt_key(run_id: str, attempt: int) -> str:
    return f"section18:{run_id}:attempt:{attempt}"


class SourceImportService:
    def __init__(self, context: OperatorContext):
        self.context = context

    def import_pdf(
        self,
        run_id: str,
        payload: bytes,
        *,
        display_name: str,
        media_type: str = "application/pdf",
    ) -> dict[str, object]:
        run = self.context.operator.get_run(run_id)
        if run.state != "DRAFT":
            raise OperatorConflict("initial_import_requires_draft")
        name = require_token(display_name, "display_name", max_len=240)
        validation = validate_pdf_source(payload, media_type=media_type)
        if not validation.accepted:
            self.context.operator.transition(
                run_id,
                expected={"DRAFT"},
                target="BLOCKED",
                event_type="SOURCE_REJECTED",
                payload={"diagnostics": list(validation.diagnostics)},
            )
            return {
                "run": self.context.operator.get_run(run_id).to_safe_dict(),
                "validation": validation.to_safe_dict(),
                "canonical_job": None,
            }

        service = self.context.job_service()
        try:
            key = _attempt_key(run_id, 1)
            job = service.submit(payload, key)
        finally:
            service.close()
        bound = self.context.operator.bind_source_attempt(
            run_id,
            attempt=1,
            canonical_job_id=str(job["job_id"]),
            idempotency_key=key,
            source_hash=str(job["source_hash"]),
            source_name=name,
        )
        return {
            "run": bound.to_safe_dict(),
            "validation": validation.to_safe_dict(),
            "canonical_job": dict(job),
        }
