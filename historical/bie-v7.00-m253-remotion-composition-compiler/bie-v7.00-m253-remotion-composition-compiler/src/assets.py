def bind_assets(layers, asset_registry):
    bound=[]
    errors=[]
    for layer in layers:
        asset_id=layer.get("asset_id")
        if asset_id:
            if asset_id not in asset_registry: errors.append(f"ASSET_NOT_FOUND:{asset_id}")
            bound.append({**layer,"asset":asset_registry.get(asset_id)})
        else:
            bound.append({**layer,"asset":None})
    return {"layers":bound,"errors":errors,"valid":not errors}
