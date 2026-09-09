def cache_capabilities():
    return {
      "cache_entries_are_supported":True,
      "ttl_is_supported":True,
      "invalidation_is_supported":True,
      "consistency_modes_are_supported":True,
      "cache_aside_is_supported":True,
      "read_through_is_supported":True,
      "write_through_is_supported":True,
      "write_behind_is_supported":True,
      "distributed_state_ownership_is_supported":True,
      "replication_lag_is_supported":True,
      "stale_read_policies_are_supported":True,
      "cache_observability_is_supported":True
    }
