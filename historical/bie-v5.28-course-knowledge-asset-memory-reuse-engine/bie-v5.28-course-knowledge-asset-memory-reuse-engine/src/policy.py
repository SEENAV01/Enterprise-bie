def memory_policy():
    return {
      "canonical_records_are_versioned":True,
      "source_provenance_is_preserved":True,
      "derived_lineage_is_preserved":True,
      "semantic_reuse_is_explicit":True,
      "reuse_can_require_adaptation":True,
      "low_confidence_matches_regenerate":True,
      "invalidated_records_are_not_silently_reused":True,
      "knowledge_and_render_artifacts_can_be_reused":True,
      "memory_is_domain_agnostic":True
    }
