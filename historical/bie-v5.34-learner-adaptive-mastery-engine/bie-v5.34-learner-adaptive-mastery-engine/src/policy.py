def adaptive_policy():
    return {
      "learner_state_is_separate_from_canonical_content":True,
      "mastery_requires_learning_evidence":True,
      "misconceptions_can_trigger_remediation":True,
      "mastered_objectives_can_be_skipped_or_advanced":True,
      "unmastered_objectives_can_trigger_review":True,
      "adaptation_preserves_prerequisites":True,
      "learner_data_does_not_mutate_source_knowledge":True,
      "adaptive_rules_are_explainable":True,
      "domain_agnostic":True
    }
