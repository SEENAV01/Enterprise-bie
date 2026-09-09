def human_review_policy():
    return {
      "review_queues_are_explicit":True,
      "reviewer_eligibility_is_checked":True,
      "evidence_packets_are_supported":True,
      "structured_decisions_are_required":True,
      "escalation_is_supported":True,
      "overrides_require_explicit_approval":True,
      "review_slas_are_supported":True,
      "review_decisions_are_auditable":True,
      "human_and_automated_gates_are_composable":True
    }
