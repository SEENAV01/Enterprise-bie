def transaction_policy():
    return {
      "sagas_are_supported":True,
      "compensating_actions_are_supported":True,
      "saga_state_is_explicit":True,
      "reverse_compensation_order_is_supported":True,
      "outbox_records_are_supported":True,
      "inbox_deduplication_is_supported":True,
      "retry_policies_are_supported":True,
      "consistency_modes_are_explicit":True,
      "distributed_transaction_boundaries_are_identifiable":True,
      "partial_success_can_be_represented":True
    }
