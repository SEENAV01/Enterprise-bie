from __future__ import annotations

import hashlib

from bie.infrastructure.artifact_store import BlobRef

from .context import OperatorContext
from .models import OperatorConflict, OperatorError
from .source_import import _attempt_key


class RetryService:
    def __init__(self, context: OperatorContext):
        self.context = context

    def retry(self, run_id: str) -> dict[str, object]:
        run = self.context.operator.get_run(run_id)
        if run.state != "FAILED":
            raise OperatorConflict("retry_requires_failed_run")
        prior = self.context.operator.attempt(run_id)
        service = self.context.job_service()
        try:
            source_id = "source-" + prior.canonical_job_id.removeprefix("job-")
            source = service.persistence.load_artifact(source_id)
            payload = service.cas.get_bytes(BlobRef(
                source.blob_algorithm, source.blob_digest, source.blob_size
            ))
            digest = hashlib.sha256(payload).hexdigest()
            if digest != prior.source_hash or digest != run.source_hash:
                raise OperatorError("retry_source_integrity_failed")
            next_attempt = run.attempt + 1
            key = _attempt_key(run_id, next_attempt)
            job = service.submit(payload, key)
        finally:
            service.close()
        updated = self.context.operator.bind_source_attempt(
            run_id,
            attempt=next_attempt,
            canonical_job_id=str(job["job_id"]),
            idempotency_key=key,
            source_hash=str(job["source_hash"]),
            source_name=run.source_name or "source.pdf",
            retry_of_job_id=prior.canonical_job_id,
        )
        return {
            "run": updated.to_safe_dict(),
            "retry_of_job_id": prior.canonical_job_id,
            "new_canonical_job_id": job["job_id"],
            "source_hash": job["source_hash"],
            "prior_attempt_preserved": True,
        }
