from retries import should_retry
from idempotency import already_completed
from recovery import recover_expired_leases

def compile_fault_tolerance(queue,leases,now,job_id=None,
                            error=None,attempt=1,retry=None,
                            completed_keys=None,key=None):
    retry=retry or {"max_attempts":3,"backoff_seconds":10}
    recovery=recover_expired_leases(queue,leases,now)
    retry_allowed=(should_retry(error,attempt,retry)
                   if error is not None else False)
    duplicate=(already_completed(key,completed_keys or [])
               if key else False)
    return {"schema_version":"5.60",
            "recovery":recovery,
            "retry":{"allowed":retry_allowed},
            "idempotency":{"already_completed":duplicate},
            "quality_gate":{"valid":not duplicate,
                            "errors":["DUPLICATE_EFFECT"]
                            if duplicate else []}}
