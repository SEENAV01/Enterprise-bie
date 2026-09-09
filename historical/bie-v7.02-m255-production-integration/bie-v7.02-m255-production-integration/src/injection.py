def inject_assets(scene_layers, asset_registry):
    injected=[]; errors=[]
    for layer in scene_layers:
        aid=layer.get("asset_id")
        item={**layer}
        if aid:
            if aid not in asset_registry: errors.append(f"ASSET_NOT_FOUND:{aid}")
            else: item["resolved_asset"]=asset_registry[aid]
        injected.append(item)
    return {"layers":injected,"valid":not errors,"errors":errors}

def inject_audio(segments,audio_registry):
    resolved=[]; errors=[]
    for s in segments:
        aid=s.get("audio_id")
        item={**s}
        if aid:
            if aid not in audio_registry: errors.append(f"AUDIO_NOT_FOUND:{aid}")
            else: item["resolved_audio"]=audio_registry[aid]
        resolved.append(item)
    return {"segments":resolved,"valid":not errors,"errors":errors}
