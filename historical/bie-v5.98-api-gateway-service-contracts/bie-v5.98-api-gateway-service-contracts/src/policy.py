def api_policy():
    return {
      "versioned_apis_are_supported":True,
      "request_response_contracts_are_explicit":True,
      "authentication_boundaries_are_supported":True,
      "authorization_scopes_are_supported":True,
      "rate_limits_are_supported":True,
      "idempotency_is_supported":True,
      "standard_error_codes_are_supported":True,
      "pagination_is_supported":True,
      "compatibility_checks_are_supported":True,
      "correlation_ids_are_supported":True
    }
