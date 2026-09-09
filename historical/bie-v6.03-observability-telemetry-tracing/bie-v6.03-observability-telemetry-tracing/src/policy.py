def observability_policy():
    return {
      "structured_logs_are_supported":True,
      "metrics_are_supported":True,
      "distributed_traces_are_supported":True,
      "spans_are_supported":True,
      "trace_context_propagation_is_supported":True,
      "correlation_propagation_is_supported":True,
      "workflow_observability_is_supported":True,
      "worker_telemetry_is_supported":True,
      "health_signals_are_supported":True,
      "diagnostic_context_is_supported":True,
      "secret_redaction_in_logs_is_supported":True
    }
