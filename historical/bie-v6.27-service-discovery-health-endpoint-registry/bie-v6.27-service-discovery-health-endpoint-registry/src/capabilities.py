def discovery_capabilities():
    return {
      "service_registration_is_supported":True,
      "endpoint_registration_is_supported":True,
      "endpoint_leases_are_supported":True,
      "health_status_is_supported":True,
      "readiness_liveness_startup_probes_are_supported":True,
      "service_metadata_is_supported":True,
      "discovery_queries_are_supported":True,
      "endpoint_draining_is_supported":True,
      "registry_entries_are_supported":True,
      "registry_observability_is_supported":True
    }
