def routing_policy():
    return {
      "provider_neutral":True,
      "capability_matching_required":True,
      "quality_constraints_enforced":True,
      "cost_constraints_supported":True,
      "latency_constraints_supported":True,
      "reliability_constraints_enforced":True,
      "context_compatibility_checked":True,
      "fallback_chain_is_explicit":True,
      "routing_decisions_are_auditable":True,
      "hard_budget_can_block_expensive_models":True
    }
