def render_contract(contract_id,asset_ref,representation_type,
                    inputs=None,outputs=None,quality=None,
                    timing=None,interaction=None,accessibility=None,
                    constraints=None):
    return {"contract_id":contract_id,"asset_ref":asset_ref,
            "representation_type":representation_type,
            "inputs":inputs or [],"outputs":outputs or [],
            "quality":quality or {},"timing":timing or {},
            "interaction":interaction or {},
            "accessibility":accessibility or {},
            "constraints":constraints or {}}
