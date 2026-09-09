def durable_workflow_policy():
    return {
      "workflow_state_is_explicit":True,
      "state_transitions_are_validated":True,
      "checkpoints_are_persistable":True,
      "long_running_workflows_are_supported":True,
      "timeouts_are_explicit":True,
      "partial_failure_is_detectable":True,
      "compensation_actions_are_supported":True,
      "compensation_order_is_reverse_completion_order":True,
      "recovery_can_resume_from_checkpoint":True,
      "recovery_actions_are_explicit":True
    }
