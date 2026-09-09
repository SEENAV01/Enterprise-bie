def capabilities():
    return {"shared_state_store":True,"optimistic_concurrency":True,
            "versioned_revisions":True,"checkpoints":True,"state_merge":True,
            "consistency_checks":True,"checkpoint_recovery":True,"event_replay":True}
