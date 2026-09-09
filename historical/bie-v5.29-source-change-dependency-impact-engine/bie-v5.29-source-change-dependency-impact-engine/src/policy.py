def impact_policy():
    return {
      "source_changes_are_explicit":True,
      "dependency_graph_drives_impact":True,
      "downstream_artifacts_can_be_invalidated":True,
      "minimal_regeneration_is_preferred":True,
      "unchanged_artifacts_are_protected":True,
      "high_risk_changes_can_block_automation":True,
      "low_confidence_changes_can_require_review":True,
      "semantic_change_can_trigger_reassessment":True,
      "source_change_does_not_silently_rewrite_history":True
    }
