def evaluation_policy():
    return {
      "golden_datasets_are_versioned":True,
      "rubrics_are_versioned":True,
      "task_specific_evaluation_is_supported":True,
      "quality_thresholds_are_explicit":True,
      "regressions_can_block_promotion":True,
      "model_comparison_is_supported":True,
      "evaluation_provenance_is_recorded":True,
      "evaluation_is_distinct_from_routing_metadata":True,
      "measured_quality_can_feed_routing":True
    }
