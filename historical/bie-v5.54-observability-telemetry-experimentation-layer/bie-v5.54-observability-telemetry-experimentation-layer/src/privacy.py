def telemetry_policy():
    return {
      "collect_only_declared_events":True,
      "event_schema_is_explicit":True,
      "learner_identity_should_be_minimized":True,
      "sensitive_fields_should_not_be_required_for_core_metrics":True,
      "purpose_limitation_is_required":True,
      "retention_should_be_configurable":True,
      "raw_events_and_aggregates_are_separable":True
    }
