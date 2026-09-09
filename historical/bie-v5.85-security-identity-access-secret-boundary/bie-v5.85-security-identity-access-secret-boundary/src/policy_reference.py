def security_controls():
    return {
      "authentication_context_required":True,
      "authorization_is_resource_scoped":True,
      "deny_by_default":True,
      "least_privilege":True,
      "service_identities_supported":True,
      "capability_checks_supported":True,
      "secret_references_supported":True,
      "secret_values_not_embedded_in_policy":True,
      "privileged_operations_are_explicit":True,
      "inactive_principals_are_denied":True
    }
