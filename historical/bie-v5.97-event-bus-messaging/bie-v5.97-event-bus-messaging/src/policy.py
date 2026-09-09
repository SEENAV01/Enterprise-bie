def messaging_policy():
    return {
      "typed_events_are_supported":True,
      "commands_are_supported":True,
      "correlation_ids_are_supported":True,
      "causation_ids_are_supported":True,
      "topics_and_subscriptions_are_supported":True,
      "delivery_semantics_are_explicit":True,
      "acknowledgments_are_supported":True,
      "idempotent_consumers_are_supported":True,
      "delivery_retries_are_supported":True,
      "dead_letter_handling_is_supported":True,
      "replay_is_supported":True,
      "partition_ordering_is_supported":True
    }
