def production_build_policy():
    return {
      "dependency_graph_is_authoritative":True,
      "parallel_work_is_supported":True,
      "stable_hashing_is_supported":True,
      "cache_reuse_is_supported":True,
      "downstream_invalidation_is_supported":True,
      "build_manifests_are_supported":True,
      "resumable_builds_are_supported":True,
      "deterministic_build_inputs_are_preferred":True,
      "domain_agnostic":True
    }
