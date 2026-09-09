def traffic_policy():
    return {
      "service_registration_is_supported":True,
      "service_discovery_is_supported":True,
      "health_probes_are_supported":True,
      "readiness_and_liveness_are_supported":True,
      "health_aware_routing_is_supported":True,
      "weighted_routing_is_supported":True,
      "circuit_breakers_are_supported":True,
      "traffic_draining_is_supported":True,
      "graceful_degradation_is_supported":True,
      "unhealthy_instances_can_be_excluded":True
    }
