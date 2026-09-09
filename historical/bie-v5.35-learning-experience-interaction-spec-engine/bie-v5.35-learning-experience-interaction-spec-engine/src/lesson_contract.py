def lesson_contract(lesson_id,objective_refs=None,
                    interaction_refs=None,asset_requirements=None,
                    accessibility=None):
    return {"lesson_id":lesson_id,
            "objective_refs":objective_refs or [],
            "interaction_refs":interaction_refs or [],
            "asset_requirements":asset_requirements or [],
            "accessibility":accessibility or {}}
