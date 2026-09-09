def crypto_capabilities():
    return {
      "secret_references_are_supported":True,
      "key_versioning_is_supported":True,
      "rotation_is_supported":True,
      "expiration_is_supported":True,
      "revocation_is_supported":True,
      "encryption_metadata_is_supported":True,
      "signing_metadata_is_supported":True,
      "verification_contracts_are_supported":True,
      "access_policies_are_supported":True,
      "secret_redaction_is_supported":True,
      "material_lifecycle_is_explicit":True
    }
