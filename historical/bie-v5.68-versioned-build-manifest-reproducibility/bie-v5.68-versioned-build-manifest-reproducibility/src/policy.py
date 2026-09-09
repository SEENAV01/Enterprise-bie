def reproducibility_policy():
    return {
      "manifest_is_versioned":True,
      "canonical_serialization_is_used":True,
      "manifest_digest_is_deterministic":True,
      "inputs_are_explicit":True,
      "asset_versions_are_explicit":True,
      "generator_and_renderer_versions_are_explicit":True,
      "dependencies_can_be_locked":True,
      "configuration_is_explicit":True,
      "policies_are_explicit":True,
      "seeds_can_be_recorded":True,
      "cache_keys_can_derive_from_manifest":True,
      "rollback_targets_are_recorded":True,
      "domain_agnostic":True
    }
