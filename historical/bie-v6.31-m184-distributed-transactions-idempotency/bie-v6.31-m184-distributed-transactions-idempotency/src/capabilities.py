def transaction_capabilities():
    return {
      "transaction_boundaries_are_supported":True,
      "atomic_commit_abort_is_supported":True,
      "idempotency_keys_are_supported":True,
      "request_deduplication_is_supported":True,
      "inbox_pattern_is_supported":True,
      "outbox_pattern_is_supported":True,
      "exactly_once_effect_contract_is_supported":True,
      "saga_compensation_is_supported":True,
      "retry_recovery_is_supported":True,
      "transaction_observability_is_supported":True
    }
