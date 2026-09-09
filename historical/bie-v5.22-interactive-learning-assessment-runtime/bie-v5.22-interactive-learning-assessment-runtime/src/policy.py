def runtime_policy():
    return {
      "responses_are_persisted":True,
      "evaluation_is_explicit":True,
      "rubric_items_can_require_review":True,
      "feedback_follows_evaluation":True,
      "hints_are_attempt_aware":True,
      "mastery_updates_are_bounded":True,
      "repeated_errors_can_signal_misconceptions":True,
      "learner_state_persists_across_lessons":True,
      "assessment_does_not_change_source_truth":True
    }
