def secrets_capabilities():
    return {
      "secret_references_are_supported":True,
      "key_metadata_is_supported":True,
      "key_rotation_is_supported":True,
      "certificate_lifecycle_is_supported":True,
      "revocation_is_supported":True,
      "key_usage_policies_are_supported":True,
      "expiry_checks_are_supported":True,
      "secure_material_boundaries_are_supported":True,
      "secret_audit_events_are_supported":True
    }
