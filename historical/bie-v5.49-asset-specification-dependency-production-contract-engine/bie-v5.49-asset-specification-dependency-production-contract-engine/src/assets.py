def asset_spec(asset_id,asset_type,inputs=None,outputs=None,
               objective_refs=None,requirements=None,metadata=None):
    return {"asset_id":asset_id,"asset_type":asset_type,
            "inputs":inputs or [],"outputs":outputs or [],
            "objective_refs":objective_refs or [],
            "requirements":requirements or [],
            "metadata":metadata or {}}

def asset_types():
    return ["SCENE","ANIMATION","DIAGRAM","SIMULATION","INTERACTIVE",
            "AUDIO","NARRATION","TEXT","CHART","QUESTION","GAME_ASSET",
            "COMPOSITE"]
