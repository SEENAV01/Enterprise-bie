def execution_security_policy():
    return {
      "execution_isolation_is_explicit":True,
      "permissions_are_separate_from_generation_intent":True,
      "resource_budgets_are_enforced":True,
      "network_access_is_policy_controlled":True,
      "filesystem_access_is_boundary_controlled":True,
      "host_access_is_disabled_by_default":True,
      "privilege_escalation_is_disabled_by_default":True,
      "inputs_can_be_readonly":True,
      "outputs_are_restricted":True,
      "audit_events_are_supported":True,
      "domain_agnostic":True
    }
