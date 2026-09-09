def orchestration_policy():
    return {
      "workflows_are_dependency_aware":True,
      "jobs_are_idempotent":True,
      "worker_leases_are_required":True,
      "retries_are_policy_driven":True,
      "checkpoints_are_persisted":True,
      "concurrency_is_bounded":True,
      "partial_rebuilds_are_supported":True,
      "cycles_are_rejected":True,
      "failed_jobs_are_recoverable_or_terminal":True
    }
