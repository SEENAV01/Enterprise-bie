def regeneration_action(node_id,reason,priority="NORMAL",
                       invalidated=True):
    return {"node_id":node_id,"action":"REGENERATE",
            "reason":reason,"priority":priority,
            "invalidated":invalidated}

def minimal_plan(changed,affected,protected=None):
    protected=set(protected or [])
    return [regeneration_action(n,"DOWNSTREAM_IMPACT")
            for n in affected if n not in protected]
