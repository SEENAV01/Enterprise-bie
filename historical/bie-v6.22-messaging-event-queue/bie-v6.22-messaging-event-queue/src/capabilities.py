def messaging_capabilities():
    return {
      "topics_are_supported":True,
      "queues_are_supported":True,
      "events_are_supported":True,
      "commands_are_supported":True,
      "consumer_groups_are_supported":True,
      "delivery_semantics_are_supported":True,
      "retry_policies_are_supported":True,
      "dead_letter_handling_is_supported":True,
      "idempotency_is_supported":True,
      "scheduled_delivery_is_supported":True,
      "messaging_observability_is_supported":True
    }
