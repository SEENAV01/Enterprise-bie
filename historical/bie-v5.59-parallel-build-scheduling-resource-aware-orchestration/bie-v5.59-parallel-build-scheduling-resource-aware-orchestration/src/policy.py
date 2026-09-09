def orchestration_policy():
    return {
      "dependency_constraints_are_hard":True,
      "independent_jobs_can_run_in_parallel":True,
      "resource_capacity_is_explicit":True,
      "critical_path_is_supported":True,
      "priority_is_supported":True,
      "tool_capacity_is_supported":True,
      "budget_aware_scheduling_is_supported":True,
      "oversubscription_is_prevented":True,
      "domain_agnostic":True
    }
