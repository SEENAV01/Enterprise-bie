def workflow_definition(workflow_id, states, transitions, initial):
    if initial not in states:
        raise ValueError("INITIAL_STATE_UNKNOWN")
    return {"workflow_id":workflow_id,"states":states,
            "transitions":transitions,"initial":initial}
