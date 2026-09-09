def fallback_chain(models, capability):
    return [m for m in models if m["status"]=="ACTIVE" and capability in m["capabilities"]]

def choose_fallback(chain, failed_model_id):
    for model in chain:
        if model["model_id"]!=failed_model_id:return model
    return None
