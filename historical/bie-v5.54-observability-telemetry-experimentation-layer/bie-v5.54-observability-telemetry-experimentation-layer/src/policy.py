def observability_policy():
    return {
      "telemetry_is_separate_from_semantics":True,
      "events_are_structured":True,
      "metrics_are_derived_or_explicit":True,
      "distributed_traces_are_supported":True,
      "cost_and_latency_are_first_class":True,
      "experiments_are_explicit":True,
      "privacy_minimization_is_supported":True,
      "optimization_must_be_evidence_driven":True,
      "domain_agnostic":True
    }
