def consistency_capabilities():
    return {
      "logical_clocks_are_supported":True,
      "vector_clocks_are_supported":True,
      "versioned_state_is_supported":True,
      "conflict_detection_is_supported":True,
      "merge_policies_are_supported":True,
      "tombstones_are_supported":True,
      "anti_entropy_is_supported":True,
      "reconciliation_is_supported":True,
      "divergence_detection_is_supported":True,
      "causal_consistency_is_supported":True,
      "consistency_observability_is_supported":True
    }
