def cache_policy():
    return {
      "cache_keys_include_input_fingerprint":True,
      "cache_keys_can_include_configuration":True,
      "cache_keys_can_include_policy_version":True,
      "cached_artifacts_are_immutable":True,
      "changed_dependencies_invalidate_downstream_nodes":True,
      "unaffected_nodes_can_be_reused":True,
      "cache_entries_are_validated_before_reuse":True,
      "incremental_builds_are_supported":True
    }
