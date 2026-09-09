def qa_policy():
    return {
      "qa_is_blocking_before_final_delivery":True,
      "scene_failures_are_explicit":True,
      "regression_changes_are_detectable":True,
      "render_validation_is_required":True,
      "human_review_can_be_required":True,
      "failed_quality_gates_prevent_final_delivery":True,
      "qa_does_not_replace_domain_reasoning":True
    }
