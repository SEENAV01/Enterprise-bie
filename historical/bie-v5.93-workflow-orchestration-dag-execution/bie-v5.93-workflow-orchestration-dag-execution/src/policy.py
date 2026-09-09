def orchestration_policy():
    return {
      "dependency_dags_are_supported":True,
      "dependency_aware_scheduling_is_supported":True,
      "concurrency_limits_are_explicit":True,
      "fan_out_and_fan_in_are_supported_by_dag_model":True,
      "retries_and_backoff_are_supported":True,
      "checkpoints_are_supported":True,
      "pause_resume_cancel_are_supported":True,
      "task_leases_are_supported":True,
      "idempotency_is_supported":True,
      "execution_state_is_explicit":True
    }
