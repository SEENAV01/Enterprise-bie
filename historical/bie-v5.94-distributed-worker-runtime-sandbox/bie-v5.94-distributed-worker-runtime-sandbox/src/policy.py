def worker_policy():
    return {
      "worker_registration_is_supported":True,
      "capability_matching_is_supported":True,
      "resource_matching_is_supported":True,
      "sandbox_metadata_is_explicit":True,
      "network_policy_is_explicit":True,
      "artifact_mount_modes_are_explicit":True,
      "timeouts_are_supported":True,
      "heartbeats_are_supported":True,
      "worker_health_is_supported":True,
      "task_results_are_structured":True
    }
