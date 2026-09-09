def fault_tolerance_policy():
    return {
      "queue_state_is_persistent":True,
      "leases_prevent_unbounded_duplicate_ownership":True,
      "worker_heartbeats_are_supported":True,
      "expired_leases_are_recoverable":True,
      "retry_policy_is_explicit":True,
      "idempotency_keys_are_supported":True,
      "checkpoints_support_resume":True,
      "worker_capabilities_are_declared":True,
      "duplicate_effects_are_blocked":True,
      "exactly_once_effect_is_targeted_where_practical":True,
      "domain_agnostic":True
    }
