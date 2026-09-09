def capabilities():
    return {
        "idempotent_job_effects":True,
        "versioned_state":True,
        "compare_and_set":True,
        "artifact_locks":True,
        "leases":True,
        "fencing_tokens":True,
        "stale_writer_protection":True,
        "state_reconciliation":True,
        "commit_records":True
    }
