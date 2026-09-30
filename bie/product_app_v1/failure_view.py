from __future__ import annotations

from html import escape
import json

from bie.infrastructure.artifact_store import BlobRef

from .context import OperatorContext
from .models import OperatorConflict, OperatorError

_ALLOWED = {"job_id", "source_hash", "status", "diagnostic_code"}


class FailureViewService:
    def __init__(self, context: OperatorContext):
        self.context = context

    def failure(self, run_id: str) -> dict[str, object]:
        run = self.context.operator.get_run(run_id)
        if run.state != "FAILED":
            raise OperatorConflict("run_not_failed")
        if run.canonical_job_id is None:
            raise OperatorError("canonical_job_binding_missing")
        service = self.context.job_service()
        try:
            ids = service.persistence.evidence_for_run(run.canonical_job_id)
            if not ids:
                raise OperatorError("failure_evidence_missing")
            safe: dict[str, object] | None = None
            evidence_id: str | None = None
            for eid in ids:
                record = service.persistence.load_artifact(eid)
                if record.artifact_type != "document.inspection.evidence":
                    continue
                raw = service.cas.get_bytes(BlobRef(
                    record.blob_algorithm, record.blob_digest, record.blob_size
                ))
                value = json.loads(raw.decode("utf-8"))
                if value.get("status") == "FAILED":
                    safe = {k: value[k] for k in _ALLOWED if k in value}
                    evidence_id = eid
                    break
            if safe is None or evidence_id is None:
                raise OperatorError("failure_evidence_missing")
        finally:
            service.close()
        return {
            "run_id": run_id,
            "attempt": run.attempt,
            "evidence_id": evidence_id,
            "failure": safe,
            "retry_allowed": True,
            "raw_source_exposed": False,
            "traceback_exposed": False,
        }


def render_failure_view(view: dict[str, object]) -> str:
    failure = dict(view["failure"])
    rows = "".join(
        f"<tr><th scope='row'>{escape(str(k))}</th><td>{escape(str(v))}</td></tr>"
        for k, v in sorted(failure.items())
    )
    return (
        "<section aria-labelledby='failure-title' class='failure-view'>"
        "<h2 id='failure-title'>Run failure</h2>"
        f"<p>Evidence: <code>{escape(str(view['evidence_id']))}</code></p>"
        f"<table><tbody>{rows}</tbody></table>"
        "<p>No source document text or traceback is exposed by this view.</p>"
        "</section>"
    )
