def cache_capabilities():
    return {
      "cache_keys_are_supported":True,
      "ttl_is_supported":True,
      "invalidation_is_supported":True,
      "cache_consistency_modes_are_supported":True,
      "read_through_is_supported":True,
      "write_through_is_supported":True,
      "materialized_views_are_supported":True,
      "stampede_protection_is_supported":True,
      "cache_observability_is_supported":True
    }
