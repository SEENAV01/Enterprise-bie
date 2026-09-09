def adaptive_path_policy():
    return {
      "learner_state_drives_action_selection":True,
      "multiple_candidate_actions_are_supported":True,
      "prerequisites_can_constrain_paths":True,
      "content_availability_can_constrain_paths":True,
      "actions_are_ranked_not_hardcoded":True,
      "alternatives_are_preserved":True,
      "skip_is_a_valid_action":True,
      "representation_change_is_a_valid_action":True,
      "path_is_not_required_to_be_linear":True,
      "domain_agnostic":True
    }
