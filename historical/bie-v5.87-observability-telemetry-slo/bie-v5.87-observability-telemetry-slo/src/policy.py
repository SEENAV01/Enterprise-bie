def observability_policy():
    return {
      "logs_are_structured":True,
      "metrics_are_supported":True,
      "distributed_tracing_is_supported":True,
      "correlation_is_first_class":True,
      "slis_are_explicit":True,
      "slos_are_explicit":True,
      "error_budgets_are_calculable":True,
      "alerts_are_rule_based":True,
      "health_and_readiness_are_supported":True,
      "cost_telemetry_is_supported":True
    }
