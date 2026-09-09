def asset_registry_policy():
    return {
      "assets_are_versioned":True,
      "assets_have_stable_content_identity":True,
      "dependencies_are_explicit":True,
      "downstream_invalidation_is_supported":True,
      "dependency_aware_rebuild_is_supported":True,
      "cache_keys_include_inputs_versions_and_parameters":True,
      "rebuild_order_is_dependency_aware":True,
      "dependency_cycles_are_rejected":True,
      "domain_agnostic":True
    }
