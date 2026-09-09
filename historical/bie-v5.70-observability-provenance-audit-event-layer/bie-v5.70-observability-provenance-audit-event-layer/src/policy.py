def audit_policy():
    return {
      "events_are_append_only":True,
      "event_identity_is_explicit":True,
      "timestamps_are_recorded":True,
      "actors_are_recorded":True,
      "correlation_ids_are_supported":True,
      "state_transitions_can_be_recorded":True,
      "evidence_references_are_supported":True,
      "build_and_policy_versions_can_be_attached":True,
      "entity_lineage_is_queryable":True,
      "observability_records_are_supported":True,
      "domain_agnostic":True
    }
