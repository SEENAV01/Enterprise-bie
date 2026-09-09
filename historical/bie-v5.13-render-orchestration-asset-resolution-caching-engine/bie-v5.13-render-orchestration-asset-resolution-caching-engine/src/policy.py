def orchestration_policy():
    return {
      "content_addressed_cache":True,
      "dependency_graph_is_explicit":True,
      "missing_assets_block_render":True,
      "scene_jobs_are_independently_retryable":True,
      "transient_failures_are_retryable":True,
      "validation_failures_are_not_retried_blindly":True,
      "cached_scenes_are_not_re_rendered":True,
      "final_assembly_is_ordered":True
    }
