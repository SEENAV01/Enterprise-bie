def orchestrator_capabilities():
    return {
        "end_to_end_lesson_state_machine":True,
        "stage_contracts":True,
        "artifact_registry":True,
        "state_events":True,
        "checkpoint_resume":True,
        "bounded_failure_policy":True,
        "provenance":True,
        "final_verification":True
    }
