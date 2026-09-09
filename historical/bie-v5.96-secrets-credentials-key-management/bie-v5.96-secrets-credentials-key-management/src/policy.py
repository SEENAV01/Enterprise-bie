def secrets_policy():
    return {
      "secrets_are_reference_only":True,
      "scoped_credentials_are_supported":True,
      "short_lived_grants_are_supported":True,
      "grant_expiration_is_explicit":True,
      "revocation_is_supported":True,
      "rotation_metadata_is_supported":True,
      "worker_injection_boundary_is_explicit":True,
      "raw_secrets_are_excluded_from_injection_contract":True,
      "audit_events_are_redaction_safe":True,
      "credential_leases_are_supported":True
    }
