def configuration_policy():
    return {
      "configuration_is_typed_by_schema":True,
      "snapshots_are_immutable":True,
      "configuration_has_content_digest":True,
      "feature_flags_are_explicit":True,
      "experiment_assignments_are_deterministic":True,
      "compatibility_is_checkable":True,
      "configuration_references_are_recorded":True,
      "reproducibility_includes_relevant_flags":True,
      "domain_agnostic":True
    }
