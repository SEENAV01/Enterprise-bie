def asset_registry_policy():
    return {
      "asset_identity_is_explicit":True,
      "versions_are_explicit":True,
      "content_hashes_are_supported":True,
      "provenance_is_explicit":True,
      "transformations_are_versioned":True,
      "semantic_relationships_are_supported":True,
      "consumer_relationships_are_supported":True,
      "duplicate_versions_are_rejected":True,
      "impact_analysis_is_supported":True,
      "domain_agnostic":True
    }
