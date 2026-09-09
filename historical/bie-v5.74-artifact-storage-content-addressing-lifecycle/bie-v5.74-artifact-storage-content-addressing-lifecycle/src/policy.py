def artifact_storage_policy():
    return {
      "artifact_identity_is_content_addressed":True,
      "artifacts_are_immutable":True,
      "duplicate_bytes_are_deduplicated":True,
      "lifecycle_states_are_explicit":True,
      "promotion_requires_validation":True,
      "released_artifacts_are_protected":True,
      "referenced_artifacts_are_protected_from_gc":True,
      "deletion_requires_gc_eligibility":True,
      "lineage_parents_are_recorded":True
    }
