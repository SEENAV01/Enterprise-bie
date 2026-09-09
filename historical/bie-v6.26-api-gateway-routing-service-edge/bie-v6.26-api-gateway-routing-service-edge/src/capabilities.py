def gateway_capabilities():
    return {
      "route_registration_is_supported":True,
      "api_versioning_is_supported":True,
      "auth_handoff_is_supported":True,
      "rate_limit_integration_is_supported":True,
      "request_transformation_is_supported":True,
      "upstream_selection_is_supported":True,
      "health_aware_routing_is_supported":True,
      "gateway_retries_are_supported":True,
      "circuit_breakers_are_supported":True,
      "edge_observability_is_supported":True
    }
