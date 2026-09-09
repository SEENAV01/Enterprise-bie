def workflow_capabilities():
    return {
      "workflow_definitions_are_supported":True,
      "state_machines_are_supported":True,
      "durable_checkpoints_are_supported":True,
      "timers_are_supported":True,
      "wait_conditions_are_supported":True,
      "saga_compensation_is_supported":True,
      "cancellation_is_supported":True,
      "pause_resume_is_supported":True,
      "human_approval_gates_are_supported":True,
      "deterministic_replay_inputs_are_supported":True
    }
