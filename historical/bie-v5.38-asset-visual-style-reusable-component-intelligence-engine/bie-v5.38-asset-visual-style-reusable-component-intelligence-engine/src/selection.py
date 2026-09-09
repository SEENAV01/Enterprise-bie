def asset_score(asset,semantic_tags=None):
    wanted=set(semantic_tags or [])
    tags=set(asset.get("semantic_tags",[]))
    return len(wanted & tags)

def select_assets(assets,semantic_tags=None):
    return sorted(assets,key=lambda a:asset_score(a,semantic_tags),
                  reverse=True)

def component_compatibility(component,semantic_contract):
    required=set(semantic_contract or {})
    provided=set(component.get("semantic_contract",{}))
    return {"compatible":required.issubset(provided),
            "missing":sorted(required-provided)}
