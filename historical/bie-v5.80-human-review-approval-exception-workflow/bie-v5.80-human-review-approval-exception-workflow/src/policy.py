def human_review_policy():
    return {
      "review_states_are_explicit":True,
      "reviewer_roles_are_authorized":True,
      "annotations_are_structured":True,
      "critical_cases_can_escalate":True,
      "rejections_are_recorded":True,
      "overrides_require_rationale":True,
      "overrides_require_authority":True,
      "dual_control_is_supported":True,
      "review_provenance_is_recorded":True,
      "human_actions_do_not_silently_bypass_gates":True
    }
