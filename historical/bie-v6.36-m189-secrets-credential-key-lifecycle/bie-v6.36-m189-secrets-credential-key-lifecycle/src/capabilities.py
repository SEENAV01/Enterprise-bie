def key_lifecycle_capabilities():
    return {
      "secret_references":True,
      "key_records":True,
      "key_versioning":True,
      "rotation":True,
      "revocation":True,
      "credential_leases":True,
      "envelope_encryption_boundaries":True,
      "secure_retrieval_contracts":True,
      "lifecycle_audit":True,
      "key_observability":True
    }
