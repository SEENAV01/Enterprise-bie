def artifact_storage_policy():
    return {
      "content_addressed_identity_is_supported":True,
      "immutable_artifacts_are_supported":True,
      "storage_locations_are_explicit":True,
      "cache_keys_are_explicit":True,
      "cache_expiry_is_supported":True,
      "deduplication_is_supported":True,
      "checksummed_transfer_is_supported":True,
      "retention_policies_are_supported":True,
      "tiering_is_supported":True,
      "reference_signatures_are_supported":True,
      "integrity_verification_is_supported":True
    }
