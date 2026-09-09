def eventing_policy():
    return {
      "events_have_unique_ids":True,
      "events_are_correlatable":True,
      "causation_is_recorded":True,
      "subscriptions_are_explicit":True,
      "delivery_is_idempotent":True,
      "retry_with_backoff_is_supported":True,
      "dead_letter_is_supported":True,
      "notification_delivery_state_is_recorded":True,
      "approval_signals_are_machine_detectable":True,
      "event_store_is_append_only_reference_model":True
    }
