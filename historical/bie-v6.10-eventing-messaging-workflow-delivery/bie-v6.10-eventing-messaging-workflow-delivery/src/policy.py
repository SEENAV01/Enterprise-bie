def eventing_capabilities():
    return {
      "events_are_supported":True,
      "topics_are_supported":True,
      "queues_are_supported":True,
      "delivery_semantics_are_supported":True,
      "idempotency_is_supported":True,
      "ordering_policies_are_supported":True,
      "dead_letter_is_supported":True,
      "replay_is_supported":True,
      "backpressure_is_supported":True,
      "workflow_delivery_contracts_are_supported":True
    }
