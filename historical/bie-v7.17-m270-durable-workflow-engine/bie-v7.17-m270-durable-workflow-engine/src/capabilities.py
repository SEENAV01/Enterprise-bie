def capabilities():
    return {"workflow_definitions":True,"state_machine_execution":True,
            "event_transitions":True,"timeouts":True,"compensation":True,
            "durable_persistence":True,"resume":True,"recovery_replay":True}
