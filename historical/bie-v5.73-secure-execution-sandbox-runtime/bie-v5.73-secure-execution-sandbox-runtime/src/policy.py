def runtime_policy():
    return {
      "generated_code_runs_in_sandbox":True,
      "default_network_mode":"DENY",
      "filesystem_write_is_artifact_only":True,
      "process_permissions_are_explicit":True,
      "resource_limits_are_required":True,
      "timeouts_are_required":True,
      "output_size_is_limited":True,
      "promotion_requires_validation_reference":True,
      "production_execution_is_not_implicit":True
    }
