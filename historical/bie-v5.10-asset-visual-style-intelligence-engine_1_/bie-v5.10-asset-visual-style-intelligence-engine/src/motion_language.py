def motion_rule(rule_id, semantic_trigger, motion,
                duration_policy="CONTENT_DRIVEN"):
    return {
      "rule_id":rule_id,
      "semantic_trigger":semantic_trigger,
      "motion":motion,
      "duration_policy":duration_policy
    }
