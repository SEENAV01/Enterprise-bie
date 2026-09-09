def capabilities():
    return {"saga_orchestration":True,"transaction_lifecycle":True,
            "commit_rollback":True,"compensation_policies":True,
            "partial_failure_handling":True,"idempotent_effects":True,
            "exactly_once_effect_contract":True}
