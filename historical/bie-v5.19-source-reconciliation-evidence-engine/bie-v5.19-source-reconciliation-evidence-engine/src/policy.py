def evidence_policy():
    return {
      "claims_require_source_refs":True,
      "evidence_is_separate_from_claims":True,
      "contradictions_are_explicit":True,
      "uncertainty_is_explicit":True,
      "source_weighting_is_configurable":True,
      "unresolved_claims_can_trigger_review":True,
      "no_silent_reconciliation":True,
      "evidence_packets_feed_domain_reasoning":True
    }
