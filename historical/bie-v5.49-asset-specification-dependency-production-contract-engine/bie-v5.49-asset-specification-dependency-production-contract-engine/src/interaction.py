def interaction_contract(inputs=None,states=None,events=None,
                          outputs=None):
    return {"inputs":inputs or [],"states":states or [],
            "events":events or [],"outputs":outputs or []}
