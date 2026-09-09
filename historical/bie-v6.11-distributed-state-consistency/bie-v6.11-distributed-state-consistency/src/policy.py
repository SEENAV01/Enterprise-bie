def state_capabilities():
    return {
      "versioned_entities_are_supported":True,
      "optimistic_concurrency_is_supported":True,
      "sequence_numbers_are_supported":True,
      "version_vectors_are_supported":True,
      "transaction_contracts_are_supported":True,
      "idempotent_transitions_are_supported":True,
      "consistency_contracts_are_supported":True,
      "conflict_detection_is_supported":True,
      "conflict_resolution_is_supported":True,
      "reconciliation_is_supported":True
    }
