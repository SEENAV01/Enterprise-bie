def outcome(outcome_id,learner_id,action_id,
            target_refs=None,pre_state=None,post_state=None,
            delta=None,latency=None,cost=None,metadata=None):
    return {"outcome_id":outcome_id,"learner_id":learner_id,
            "action_id":action_id,"target_refs":target_refs or [],
            "pre_state":pre_state or {},"post_state":post_state or {},
            "delta":delta or {},"latency":latency,"cost":cost,
            "metadata":metadata or {}}
