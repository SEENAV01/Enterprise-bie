def routing_decision(task_id,requirements,
                    selected_model,fallback_chain,
                    policy_version,reason):
    return {"schema_version":"5.78",
            "task_id":task_id,
            "requirements":requirements,
            "selected_model":selected_model,
            "fallback_chain":fallback_chain,
            "policy_version":policy_version,
            "reason":reason}
